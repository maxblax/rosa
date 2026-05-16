#!/usr/bin/env python
"""Amelioration 2.2 — Selection multiple des besoins exprimes.

Cocher Alimentaire + Vestimentaire, soumettre, verifier que les deux codes
sont stockes et affiches sur la page detail.
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
    from beneficiaries.models import Beneficiary, Interaction

    b = Beneficiary.objects.first()
    pk = b.pk
    Interaction.objects.filter(beneficiary_id=pk, title="Test multi-needs").delete()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Amelioration 2.2 — Selection multiple besoins:")
            page.goto(f"{BASE_URL}/beneficiaires/{pk}/interactions/new/")
            page.wait_for_load_state("domcontentloaded")
            page.fill("#id_title", "Test multi-needs")
            page.fill("#id_description", "Multi needs test")
            # Cocher ALIMENTAIRE + VESTIMENTAIRE
            page.check('input[name="primary_need"][value="ALIMENTAIRE"]')
            page.check('input[name="primary_need"][value="VESTIMENTAIRE"]')
            page.click('button[type="submit"]:has-text("Enregistrer")')
            page.wait_for_load_state("domcontentloaded")
        finally:
            browser.close()

    inter = Interaction.objects.filter(beneficiary_id=pk, title="Test multi-needs").first()
    assert inter is not None, "Interaction non creee"
    assert inter.primary_need == "ALIMENTAIRE,VESTIMENTAIRE", f"primary_need={inter.primary_need!r}"
    assert inter.primary_need_list == ["ALIMENTAIRE", "VESTIMENTAIRE"]
    assert "Alimentaire" in inter.primary_need_labels and "Vestimentaire" in inter.primary_need_labels
    print(f"  OK: primary_need = {inter.primary_need!r}")
    inter.delete()
    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
