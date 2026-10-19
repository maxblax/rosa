#!/usr/bin/env python
"""Amelioration 2.3 — Ajout de membres adultes au foyer.

Cree un beneficiaire, sur la page edit ajoute un adulte via le bouton
"Ajouter un adulte", soumet, et verifie la persistance + l'affichage
sur la page detail.
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


def create_beneficiary(page, first_name, last_name):
    page.goto(f"{BASE_URL}/beneficiaires/new/")
    page.wait_for_load_state("domcontentloaded")
    page.check("#id_gdpr_consent")
    page.fill("#id_first_name", first_name)
    page.fill("#id_last_name", last_name)
    page.click('button[type="submit"]:has-text("Créer")')
    page.wait_for_load_state("domcontentloaded")
    parts = page.url.rstrip("/").split("/")
    return int(parts[-1])


def main():
    unique = uuid.uuid4().hex[:8]
    adult_last_name = f"DUPONT{unique}"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Amelioration 2.3 — Membres adultes du foyer:")
            pk = create_beneficiary(page, "E2E", f"HH{unique}")

            page.goto(f"{BASE_URL}/beneficiaires/{pk}/edit/")
            page.wait_for_load_state("domcontentloaded")
            # Cliquer "Ajouter un adulte"
            page.click("#add-adult-btn")
            # Remplir le formulaire
            page.fill('input[name="adults-0-first_name"]', "Sophie")
            page.fill('input[name="adults-0-last_name"]', adult_last_name)
            page.select_option('select[name="adults-0-relationship"]', "CONJOINT")
            page.fill('input[name="adults-0-birth_date"]', "17/03/1985")
            # Soumettre
            page.click('button[type="submit"]:has-text("Enregistrer")')
            page.wait_for_load_state("domcontentloaded")

            # Verifier la persistance sur la page detail
            page.goto(f"{BASE_URL}/beneficiaires/{pk}/")
            page.wait_for_load_state("domcontentloaded")
            body_text = page.evaluate("() => document.body.innerText")
            assert "Sophie" in body_text, "Prenom de l'adulte absent de la fiche"
            assert adult_last_name in body_text, "Nom de l'adulte absent de la fiche"
            assert "Conjoint" in body_text, "Relation (Conjoint·e) absente de la fiche"
            assert "17/03/1985" in body_text, "Date de naissance de l'adulte absente de la fiche"
            print(f"  OK: Sophie {adult_last_name} (Conjoint·e), ne le 17/03/1985, visible sur la fiche")

            # Verifier aussi la persistance a la re-ouverture de la page edit
            page.goto(f"{BASE_URL}/beneficiaires/{pk}/edit/")
            page.wait_for_load_state("domcontentloaded")
            first_name_val = page.input_value('input[name="adults-0-first_name"]')
            assert first_name_val == "Sophie", f"adults-0-first_name={first_name_val!r} apres reouverture"
            print("  OK: formulaire d'edition re-ouvert avec l'adulte pre-rempli")
        finally:
            browser.close()

    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
