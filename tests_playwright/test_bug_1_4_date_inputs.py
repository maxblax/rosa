#!/usr/bin/env python
"""Bug 1.4 — Saisie manuelle de dates (JJ/MM/AAAA).

Verifie que les champs date (birth_date, first_entry_date) acceptent
une saisie clavier au format JJ/MM/AAAA, y compris pour des annees
anciennes (ex: 2008).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date

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


def fill_and_submit(page):
    page.goto(f"{BASE_URL}/beneficiaires/new/")
    page.wait_for_load_state("domcontentloaded")
    # Verifier que c'est bien un input texte avec placeholder JJ/MM/AAAA
    inp_type = page.evaluate("() => document.getElementById('id_birth_date').type")
    assert inp_type == "text", f"birth_date devrait etre type=text, got {inp_type}"

    page.check("#id_gdpr_consent")
    page.fill("#id_first_name", "TestDate")
    page.fill("#id_last_name", "BUG14")
    page.fill("#id_birth_date", "17/03/2008")
    page.fill("#id_first_entry_date", "01-01-2020")
    page.click('button[type="submit"]:has-text("Créer")')
    page.wait_for_load_state("domcontentloaded")
    return page.url


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Bug 1.4 — Saisie manuelle dates JJ/MM/AAAA:")
            final_url = fill_and_submit(page)
        finally:
            browser.close()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rosa.settings")
    import django

    django.setup()
    from beneficiaries.models import Beneficiary

    b = Beneficiary.objects.filter(first_name="TestDate", last_name="BUG14").order_by("-id").first()
    assert b is not None, "Beneficiaire devrait avoir ete cree (final URL: %s)" % final_url
    assert b.birth_date == date(2008, 3, 17), f"birth_date={b.birth_date}"
    assert b.first_entry_date == date(2020, 1, 1), f"first_entry_date={b.first_entry_date}"
    print(f"  OK: birth_date {b.birth_date}, first_entry_date {b.first_entry_date}")

    # Cleanup
    b.delete()
    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
