#!/usr/bin/env python
"""Adultes du foyer dès la création + saisie souple des montants.

1. Création d'un bénéficiaire avec un adulte du foyer ajouté directement sur
   la page de création : l'adulte apparaît sur la fiche.
2. Don manuel : "Montant" accepte "1 234,56".
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


def body_text(page):
    return page.evaluate("() => document.body.innerText")


def check_create_with_adult(page, unique):
    adult_last_name = f"MARTIN{unique}"
    page.goto(f"{BASE_URL}/beneficiaires/new/")
    page.wait_for_load_state("domcontentloaded")
    page.check("#id_gdpr_consent")
    page.fill("#id_first_name", "E2E")
    page.fill("#id_last_name", f"CREA{unique}")
    page.click("#add-adult-btn")
    page.fill('input[name="adults-0-first_name"]', "Paul")
    page.fill('input[name="adults-0-last_name"]', adult_last_name)
    page.select_option('select[name="adults-0-relationship"]', "CONJOINT")
    page.fill('input[name="adults-0-birth_date"]', "02/05/1980")
    page.click('button[type="submit"]:has-text("Créer")')
    page.wait_for_load_state("domcontentloaded")
    assert re.search(r"/beneficiaires/\d+/$", page.url), f"Pas de redirection vers la fiche: {page.url}"
    pk = int(page.url.rstrip("/").split("/")[-1])
    text = body_text(page)
    assert adult_last_name in text, "Adulte ajouté à la création absent de la fiche"
    assert "02/05/1980" in text, "Date de naissance de l'adulte absente de la fiche"
    print(f"  OK: adulte Paul {adult_last_name} créé avec le dossier")
    return pk



def check_donation_amount(page, unique):
    donor = f"Donateur E2E {unique}"
    page.goto(f"{BASE_URL}/dons/create/")
    page.wait_for_load_state("domcontentloaded")
    page.fill("#id_donor_name", donor)
    page.fill("#id_amount", "1 234,56")
    page.select_option("#id_payment_type", "CASH")
    page.click('button[type="submit"]')
    page.wait_for_load_state("domcontentloaded")
    assert "/dons/create/" not in page.url, "Don refusé avec '1 234,56'"
    text = body_text(page)
    if donor not in text:
        page.goto(f"{BASE_URL}/dons/")
        text = body_text(page)
    assert donor in text, "Don créé introuvable"
    assert re.search(r"1\s?234[.,]56", text), "Montant 1234,56 absent"
    print("  OK: don '1 234,56' enregistré")


def main():
    unique = uuid.uuid4().hex[:8]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Adultes à la création + montants tolérants:")
            check_create_with_adult(page, unique)
            check_donation_amount(page, unique)
        finally:
            browser.close()
    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
