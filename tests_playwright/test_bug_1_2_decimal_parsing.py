#!/usr/bin/env python
"""Bug 1.2 — Les champs financiers doivent tolerer espaces, virgule, point.

Verifie que '1 200,50' / '1,234.56' / '1200' sont tous acceptes et stockes
correctement dans le snapshot financier.
"""
import os
import sys
from decimal import Decimal

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


def get_test_beneficiary_id():
    import os
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rosa.settings")
    django.setup()
    from beneficiaries.models import Beneficiary

    b = Beneficiary.objects.first()
    assert b is not None, "Need at least one beneficiary in DB"
    return b.pk


def submit_snapshot(page, pk):
    page.goto(f"{BASE_URL}/beneficiaires/{pk}/snapshot/new/")
    page.wait_for_load_state("domcontentloaded")

    # Saisies "naturelles" qui auraient ete rejetees par <input type=number>
    page.fill("#id_rsa_prime_activite", "1 200,50")
    page.fill("#id_apl", "1,234.56")
    page.fill("#id_salaire", "2000")

    page.click('button[type="submit"], input[type="submit"]')
    page.wait_for_load_state("domcontentloaded")


def verify_snapshot(pk):
    from beneficiaries.models import FinancialSnapshot

    snap = FinancialSnapshot.objects.filter(beneficiary_id=pk).order_by("-id").first()
    assert snap is not None, "Snapshot devrait avoir ete cree"
    assert snap.rsa_prime_activite == Decimal("1200.50"), (
        f"rsa_prime_activite={snap.rsa_prime_activite}, attendu 1200.50"
    )
    assert snap.apl == Decimal("1234.56"), f"apl={snap.apl}, attendu 1234.56"
    assert snap.salaire == Decimal("2000"), f"salaire={snap.salaire}, attendu 2000"
    print("  OK: '1 200,50' -> 1200.50, '1,234.56' -> 1234.56, '2000' -> 2000")
    snap.delete()


def main():
    pk = get_test_beneficiary_id()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Bug 1.2 — Parsing decimal tolerant:")
            submit_snapshot(page, pk)
        finally:
            browser.close()
    verify_snapshot(pk)
    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
