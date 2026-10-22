#!/usr/bin/env python
"""Module « Services aux bénéficiaires » de bout en bout.

1. Planning de l'épicerie : ajout d'une ouverture hebdomadaire, jauge modifiée
   pour une session et les suivantes, session ponctuelle, annulation.
2. Entretien refusé (trop de dates pour le vestiaire) : message d'erreur en haut
   de page, rien n'est enregistré.
3. Entretien : épicerie (1 date cochée sur 3 passages), vestiaire, « Autre
   soutien », demande d'aide financière.
4. Fiche : passages « 1/3 », réservation d'un passage restant, statut de l'aide.
5. Admin : validation puis versement de l'aide.
6. Liste de la session : famille présente, pointage, version imprimable.
7. Statistiques, catalogue et tableau de bord.
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


def open_grocery_planning(page, week=None):
    page.goto(f"{BASE_URL}/services/")
    page.locator("div.bg-white", has_text="Épicerie").locator('a:has-text("Planning et jauges")').first.click()
    page.wait_for_load_state("domcontentloaded")
    if week:
        page.goto(page.url.split("?")[0] + f"?week={week}")
    return page.url.split("?")[0]


def check_planning(page):
    planning_url = open_grocery_planning(page)
    page.click('a[title="Semaine suivante"]')
    page.wait_for_load_state("domcontentloaded")
    week = page.url.split("week=")[1]

    # Ajout d'une ouverture le vendredi (si absente) avec une jauge de 12
    if page.locator("#slots select[name=weekday] option[selected][value='4']").count() == 0:
        form = page.locator("#new-slot-form")
        form.locator("select[name=weekday]").select_option("4")
        form.locator("input[name=start_time]").fill("09:00")
        form.locator("input[name=end_time]").fill("12:00")
        form.locator("input[name=capacity]").fill("12")
        form.locator('button[type="submit"]').click()
        page.wait_for_load_state("domcontentloaded")
    friday = page.locator("#week-grid > div").nth(4)
    assert friday.locator(".session-card").count() >= 1, "Pas de session le vendredi après ajout de l'ouverture"
    print("  OK: ouverture du vendredi ajoutée, sessions générées")

    # Jauge de la session du mercredi à 25, appliquée aux suivantes
    wednesday = page.locator("#week-grid > div").nth(2)
    wednesday.locator('.session-card a:has-text("Modifier")').first.click()
    page.wait_for_load_state("domcontentloaded")
    page.fill("#id_capacity", "25")
    page.check("#id_apply_to_following")
    page.click('button:has-text("Enregistrer")')
    page.wait_for_load_state("domcontentloaded")
    page.click('a[title="Semaine suivante"]')
    page.wait_for_load_state("domcontentloaded")
    load = page.locator("#week-grid > div").nth(2).locator(".session-load").first.inner_text()
    assert "/25" in load, f"Jauge non reportée sur la semaine suivante: {load}"
    print("  OK: jauge 25 appliquée à la session et aux suivantes")

    # Session ponctuelle le samedi de la semaine, puis annulation
    page.goto(f"{planning_url}?week={week}")
    saturday_label = page.locator("#week-grid > div").nth(5).locator("p").first.inner_text()
    day, month = re.search(r"(\d\d)/(\d\d)", saturday_label).groups()
    year = week[:4] if not (month == "01" and week[5:7] == "12") else str(int(week[:4]) + 1)
    page.fill("#adhoc-form input[name=date]", f"{day}/{month}/{year}")
    page.fill("#adhoc-form input[name=start_time]", "10:00")
    page.click('#adhoc-form button[type="submit"]')
    page.wait_for_load_state("domcontentloaded")
    saturday = page.locator("#week-grid > div").nth(5)
    assert saturday.locator(".session-card").count() >= 1, "Session ponctuelle absente"
    saturday.locator('.session-card button:has-text("Annuler")').last.click()
    page.wait_for_load_state("domcontentloaded")
    assert page.locator("#week-grid > div").nth(5).locator('button:has-text("Rétablir")').count() >= 1
    print("  OK: session ponctuelle ajoutée puis annulée")


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
            check_planning(page)

            # Bénéficiaire avec un adulte en plus
            page.goto(f"{BASE_URL}/beneficiaires/new/")
            page.check("#id_gdpr_consent")
            page.fill("#id_first_name", "Test")
            page.fill("#id_last_name", last_name)
            page.click("#add-adult-btn")
            page.fill('input[name="adults-0-first_name"]', "Conjoint")
            page.click('button[type="submit"]:has-text("Créer")')
            page.wait_for_load_state("domcontentloaded")
            pk = int(re.search(r"/beneficiaires/(\d+)/", page.url).group(1))
            interaction_url = f"{BASE_URL}/beneficiaires/{pk}/interactions/new/"

            # 2. Entretien refusé : 2 dates de vestiaire pour 1 passage
            page.goto(interaction_url)
            page.fill("#id_title", "Entretien refusé")
            page.fill("#id_description", "Test refus")
            clothing = service_item(page, "Vestiaire")
            clothing.locator('label input[type="checkbox"]').first.check()
            clothing.locator("input.session-choice:not([disabled])").nth(0).check()
            clothing.locator("input.session-choice:not([disabled])").nth(1).check()
            assert "2 dates cochées sur 1 passage" in clothing.inner_text(), "Compteur de passages absent"
            page.click('button[type="submit"]:has-text("Enregistrer")')
            page.wait_for_load_state("domcontentloaded")
            alert = page.locator("#messages-container").inner_text()
            assert "n'a pas été enregistré" in alert and "Vestiaire" in alert, f"Message d'erreur absent: {alert}"
            print("  OK: entretien refusé avec message en haut de page")

            # 3. Entretien avec services
            page.goto(interaction_url)
            page.fill("#id_title", "Entretien services")
            page.fill("#id_description", "Test module services")
            grocery = service_item(page, "Épicerie")
            grocery.locator('label input[type="checkbox"]').first.check()
            grocery.locator("input.session-choice:not([disabled])").first.check()
            assert "1 date cochée sur 3 passages" in grocery.inner_text(), "Compteur épicerie incorrect"
            clothing = service_item(page, "Vestiaire")
            clothing.locator('label input[type="checkbox"]').first.check()
            clothing.locator("input.session-choice:not([disabled])").first.check()
            other = service_item(page, "Autre soutien")
            other.locator('label input[type="checkbox"]').first.check()
            other.locator('input[type="text"]').fill("Bouteille de gaz")
            aid = page.locator('#services-section .service-item[data-service-id="aid"]')
            aid.locator('input[type="checkbox"]').check()
            page.fill("#id_svc-aid_amount", "1 200,50")
            page.select_option("#id_svc-aid_nature", "TRANSPORT")
            page.fill("#id_svc-aid_reason", f"Carte de bus {unique}")
            page.click('button[type="submit"]:has-text("Enregistrer")')
            page.wait_for_load_state("domcontentloaded")
            assert re.search(rf"/beneficiaires/{pk}/$", page.url), f"Entretien refusé: {text(page)[:1500]}"

            # 4. Fiche bénéficiaire
            block = page.locator("#beneficiary-services")
            grocery_entry = block.locator("li", has_text="Épicerie").first
            assert "1/3 passage" in grocery_entry.inner_text(), f"Compteur fiche: {grocery_entry.inner_text()}"
            assert "Vestiaire" in block.inner_text() and "Bouteille de gaz" in block.inner_text()
            assert "En attente de validation" in block.inner_text(), "Statut de l'aide absent"
            # Réserver un passage restant, une autre semaine
            options = grocery_entry.locator(".assign-form select option")
            first_booked = grocery_entry.locator("span.rounded").first.inner_text()
            target = None
            for i in range(options.count()):
                label = options.nth(i).inner_text()
                if label.split()[1] != first_booked.split()[1]:
                    target = options.nth(i).get_attribute("value")
                    if i >= 2:
                        break
            grocery_entry.locator(".assign-form select").select_option(target)
            grocery_entry.locator('.assign-form button[type="submit"]').click()
            page.wait_for_load_state("domcontentloaded")
            grocery_entry = page.locator("#beneficiary-services li", has_text="Épicerie").first
            assert "2/3 passage" in grocery_entry.inner_text(), f"Passage non réservé: {grocery_entry.inner_text()}"
            print("  OK: entretien -> épicerie 1/3, passage restant réservé depuis la fiche (2/3)")

            # 5. Validation et versement de l'aide
            page.goto(f"{BASE_URL}/services/aides/?status=PENDING")
            page.locator("tr", has_text=last_name).locator("a").first.click()
            page.wait_for_load_state("domcontentloaded")
            page.check('#decision-form input[value="APPROVED"]')
            page.click('#decision-form button[type="submit"]')
            page.wait_for_load_state("domcontentloaded")
            assert "Validée" in page.locator("#aid-status").inner_text(), "Aide non validée"
            page.select_option("#id_payment_method", "CASH")
            page.click('#payment-form button[type="submit"]')
            page.wait_for_load_state("domcontentloaded")
            assert "Versée" in page.locator("#aid-status").inner_text(), "Aide non versée"
            page.goto(f"{BASE_URL}/beneficiaires/{pk}/")
            assert "Versée" in page.locator("#beneficiary-services").inner_text()
            print("  OK: aide validée puis versée, statut visible sur la fiche")

            # 6. Liste de la session épicerie réservée
            page.goto(f"{BASE_URL}/beneficiaires/{pk}/")
            # La liste est accessible depuis le planning ; on retrouve la session via la page services.
            open_grocery_planning(page)
            found = False
            for _ in range(4):
                cards = page.locator("#week-grid .session-card a[href*='/services/sessions/']")
                hrefs = [cards.nth(i).get_attribute("href") for i in range(cards.count())]
                for href in hrefs:
                    if "/modifier/" in href:
                        continue
                    page.goto(f"{BASE_URL}{href}")
                    if page.locator("tr", has_text=last_name.upper()).count():
                        found = True
                        break
                    page.go_back()
                if found:
                    break
                page.click('a[title="Semaine suivante"]')
                page.wait_for_load_state("domcontentloaded")
            assert found, "Famille absente des listes épicerie"
            row = page.locator("tr", has_text=last_name.upper())
            row.locator('input[value="yes"]').check()
            page.click('button:has-text("Enregistrer les présences")')
            page.wait_for_load_state("domcontentloaded")
            assert page.locator("tr", has_text=last_name.upper()).locator('input[value="yes"]').is_checked()
            page.goto(page.url.split("?")[0] + "?print=1")
            assert last_name.upper() in text(page), "Famille absente de la liste imprimable"
            print("  OK: famille sur la liste, présence pointée, liste imprimable")

            # 7. Statistiques, catalogue, tableau de bord
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
