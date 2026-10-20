#!/usr/bin/env python
"""Module « Services aux bénéficiaires » de bout en bout.

1. Entretien : inscription épicerie (3 mercredis), vestiaire (date choisie),
   orientation « Autre soutien » avec précision, demande d'aide financière.
2. Fiche bénéficiaire : inscriptions, dates et statut de l'aide visibles.
3. Admin : validation de l'aide, puis versement ; statut visible sur la fiche.
4. Liste de la session épicerie : famille présente, pointage, version imprimable.
5. Statistiques, catalogue et tableau de bord accessibles.
"""
import os
import re
import sys
import uuid

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("ROSA_BASE_URL", "http://localhost:5678")
USER = os.environ.get("ROSA_USER", "admin")
PASSWORD = os.environ.get("ROSA_PASSWORD", "admin123!")


def login(page):
    page.goto(f"{BASE_URL}/auth/login/")
    page.fill('input[name="username"]', USER)
    page.fill('input[name="password"]', PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_url(f"{BASE_URL}/")


def text(page):
    return page.evaluate("() => document.body.innerText")


def service_item(page, name):
    return page.locator("#services-section .service-item", has_text=name).first


def main():
    unique = uuid.uuid4().hex[:8]
    last_name = f"SERV{unique}"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("dialog", lambda d: d.accept())
        try:
            login(page)
            print("Module services:")

            # Bénéficiaire avec un adulte et deux enfants (sans dates : enfants via le nombre à charge)
            page.goto(f"{BASE_URL}/beneficiaires/new/")
            page.check("#id_gdpr_consent")
            page.fill("#id_first_name", "Test")
            page.fill("#id_last_name", last_name)
            page.click("#add-adult-btn")
            page.fill('input[name="adults-0-first_name"]', "Conjoint")
            page.click('button[type="submit"]:has-text("Créer")')
            page.wait_for_load_state("domcontentloaded")
            pk = int(re.search(r"/beneficiaires/(\d+)/", page.url).group(1))

            # 1. Entretien avec services
            page.goto(f"{BASE_URL}/beneficiaires/{pk}/interactions/new/")
            page.fill("#id_title", "Entretien services")
            page.fill("#id_description", "Test module services")

            grocery = service_item(page, "Épicerie")
            grocery.locator('input[type="checkbox"]').check()
            assert grocery.locator(".service-options").is_visible(), "Options épicerie non affichées"

            clothing = service_item(page, "Vestiaire")
            clothing.locator('input[type="checkbox"]').check()
            clothing.locator('input[type="radio"]:not([disabled])').first.check()

            other = service_item(page, "Autre soutien")
            other.locator('input[type="checkbox"]').check()
            other.locator('input[type="text"]').fill("Bouteille de gaz")

            aid = page.locator('#services-section .service-item[data-service-id="aid"]')
            aid.locator('input[type="checkbox"]').check()
            page.fill("#id_svc-aid_amount", "1 200,50")
            page.select_option("#id_svc-aid_nature", "TRANSPORT")
            page.fill("#id_svc-aid_reason", f"Carte de bus {unique}")
            page.click('button[type="submit"]:has-text("Enregistrer")')
            page.wait_for_load_state("domcontentloaded")
            assert re.search(rf"/beneficiaires/{pk}/$", page.url), f"Entretien refusé: {page.url}\n{text(page)[:1500]}"

            # 2. Fiche bénéficiaire
            body = text(page)
            block = page.locator("#beneficiary-services")
            block_text = block.inner_text()
            assert "Épicerie" in block_text and "Vestiaire" in block_text, "Inscriptions absentes de la fiche"
            assert "Autre soutien" in block_text and "Bouteille de gaz" in block_text, "Orientation absente"
            assert "En attente de validation" in block_text, "Statut de l'aide absent"
            grocery_dates = block.locator("li", has_text="Épicerie").first.locator("span.rounded").count()
            assert grocery_dates == 3, f"Épicerie: {grocery_dates} dates au lieu de 3"
            print("  OK: entretien -> épicerie (3 dates), vestiaire, autre soutien, aide en attente")

            # 3. Validation et versement de l'aide
            page.goto(f"{BASE_URL}/services/aides/?status=PENDING")
            page.locator("tr", has_text=f"{last_name}").locator("a").first.click()
            page.wait_for_load_state("domcontentloaded")
            assert "1200,50" in text(page).replace(" ", "").replace("1200.50", "1200,50"), "Montant absent"
            page.check('#decision-form input[value="APPROVED"]')
            page.click('#decision-form button[type="submit"]')
            page.wait_for_load_state("domcontentloaded")
            assert "Validée" in page.locator("#aid-status").inner_text(), "Aide non validée"
            page.select_option("#id_payment_method", "CASH")
            page.click('#payment-form button[type="submit"]')
            page.wait_for_load_state("domcontentloaded")
            assert "Versée" in page.locator("#aid-status").inner_text(), "Aide non versée"
            page.goto(f"{BASE_URL}/beneficiaires/{pk}/")
            assert "Versée" in page.locator("#beneficiary-services").inner_text(), "Statut versée absent de la fiche"
            print("  OK: aide validée puis versée, statut visible sur la fiche")

            # 4. Liste de la session épicerie
            page.goto(f"{BASE_URL}/services/")
            page.locator("div", has_text="Épicerie").locator('a[href*="/services/sessions/"]').first.click()
            page.wait_for_load_state("domcontentloaded")
            row = page.locator("tr", has_text=last_name.upper())
            assert row.count() == 1, "Famille absente de la liste épicerie"
            row_text = row.inner_text()
            assert re.search(r"\b2\b", row_text), f"Nombre d'adultes (2) absent: {row_text}"
            row.locator('input[value="yes"]').check()
            page.click('button:has-text("Enregistrer les présences")')
            page.wait_for_load_state("domcontentloaded")
            assert page.locator("tr", has_text=last_name.upper()).locator('input[value="yes"]').is_checked()
            session_url = page.url
            page.goto(f"{session_url}?print=1")
            assert last_name.upper() in text(page), "Famille absente de la liste imprimable"
            print("  OK: famille sur la liste épicerie, présence pointée, liste imprimable")

            # 5. Statistiques, catalogue, tableau de bord
            page.goto(f"{BASE_URL}/services/statistiques/")
            assert "Distributions" in text(page) and "Secours financiers" in text(page)
            page.goto(f"{BASE_URL}/services/catalogue/")
            assert "Vestiaire solidaire" in text(page) and "Antenne médicale" in text(page)
            page.goto(f"{BASE_URL}/")
            assert page.locator("#services-overview").count() == 1, "Encarts services absents du tableau de bord"
            print("  OK: statistiques, catalogue et tableau de bord")
        finally:
            browser.close()
    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
