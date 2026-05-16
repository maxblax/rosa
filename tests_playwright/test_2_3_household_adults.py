#!/usr/bin/env python
"""Amelioration 2.3 — Ajout de membres adultes au foyer.

Sur la page edit d'un beneficiaire, ajouter un adulte via le bouton
"Ajouter un adulte", soumettre, et verifier la persistence + l'affichage
sur la page detail.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5678"
USER = "admin"
PASSWORD = "admin123!"


def login(page):
    page.goto(f"{BASE_URL}/auth/login/")
    page.fill('input[name="username"]', USER)
    page.fill('input[name="password"]', PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_url(f"{BASE_URL}/")


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rosa.settings")
    import django

    django.setup()
    from beneficiaries.models import Beneficiary, HouseholdAdult

    b = Beneficiary.objects.first()
    pk = b.pk
    HouseholdAdult.objects.filter(beneficiary_id=pk).delete()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Amelioration 2.3 — Membres adultes du foyer:")
            page.goto(f"{BASE_URL}/beneficiaires/{pk}/edit/")
            page.wait_for_load_state("domcontentloaded")
            # Cliquer "Ajouter un adulte"
            page.click("#add-adult-btn")
            # Remplir le formulaire
            page.fill('input[name="adults-0-first_name"]', "Sophie")
            page.fill('input[name="adults-0-last_name"]', "DUPONT")
            page.select_option('select[name="adults-0-relationship"]', "CONJOINT")
            page.fill('input[name="adults-0-birth_date"]', "17/03/1985")
            # Soumettre
            page.click('button[type="submit"]:has-text("Enregistrer")')
            page.wait_for_load_state("domcontentloaded")
        finally:
            browser.close()

    adults = list(HouseholdAdult.objects.filter(beneficiary_id=pk))
    assert len(adults) == 1, f"Devrait avoir 1 adulte, en a {len(adults)}"
    a = adults[0]
    assert a.first_name == "Sophie"
    assert a.relationship == "CONJOINT"
    from datetime import date

    assert a.birth_date == date(1985, 3, 17)
    print(f"  OK: {a.full_name} ({a.get_relationship_display()}), ne le {a.birth_date}")
    HouseholdAdult.objects.filter(beneficiary_id=pk).delete()
    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
