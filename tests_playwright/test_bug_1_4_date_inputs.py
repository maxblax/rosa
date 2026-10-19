#!/usr/bin/env python
"""Bug 1.4 — Saisie manuelle de dates (JJ/MM/AAAA).

Verifie que les champs date (birth_date, first_entry_date) acceptent
une saisie clavier au format JJ/MM/AAAA, y compris pour des annees
anciennes (ex: 2008), et que les valeurs sont bien enregistrees (visibles
sur la page detail / pre-remplies sur la page edit).
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


def fill_and_submit(page, last_name):
    page.goto(f"{BASE_URL}/beneficiaires/new/")
    page.wait_for_load_state("domcontentloaded")
    # Verifier que c'est bien un input texte avec placeholder JJ/MM/AAAA
    inp_type = page.evaluate("() => document.getElementById('id_birth_date').type")
    assert inp_type == "text", f"birth_date devrait etre type=text, got {inp_type}"

    page.check("#id_gdpr_consent")
    page.fill("#id_first_name", "TestDate")
    page.fill("#id_last_name", last_name)
    page.fill("#id_birth_date", "17/03/2008")
    page.fill("#id_first_entry_date", "01-01-2020")
    page.click('button[type="submit"]:has-text("Créer")')
    page.wait_for_load_state("domcontentloaded")
    return page.url


def main():
    unique = uuid.uuid4().hex[:8]
    last_name = f"BUG14{unique}"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Bug 1.4 — Saisie manuelle dates JJ/MM/AAAA:")
            final_url = fill_and_submit(page, last_name)

            parts = final_url.rstrip("/").split("/")
            pk = int(parts[-1])

            # Verifier la persistance via la page d'edition (champs pre-remplis)
            page.goto(f"{BASE_URL}/beneficiaires/{pk}/edit/")
            page.wait_for_load_state("domcontentloaded")
            birth_date_val = page.input_value("#id_birth_date")
            first_entry_date_val = page.input_value("#id_first_entry_date")

            assert birth_date_val == "17/03/2008", f"birth_date={birth_date_val!r}"
            # first_entry_date est normalise au format JJ/MM/AAAA peu importe le
            # format de saisie (01-01-2020 -> 01/01/2020).
            assert first_entry_date_val == "01/01/2020", f"first_entry_date={first_entry_date_val!r}"
            print(f"  OK: birth_date {birth_date_val}, first_entry_date {first_entry_date_val}")
        finally:
            browser.close()

    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
