#!/usr/bin/env python
"""Bug 1.2 — Les champs financiers doivent tolerer espaces, virgule, point.

Verifie que '1 200,50' / '1,234.56' / '2000' sont tous acceptes et affiches
correctement (en Decimal normalise) sur la fiche beneficiaire apres
soumission du snapshot financier.
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


def submit_snapshot(page, pk):
    page.goto(f"{BASE_URL}/beneficiaires/{pk}/snapshot/new/")
    page.wait_for_load_state("domcontentloaded")

    # Saisies "naturelles" qui auraient ete rejetees par <input type=number>
    page.fill("#id_rsa_prime_activite", "1 200,50")
    page.fill("#id_apl", "1,234.56")
    page.fill("#id_salaire", "2000")

    page.click('button[type="submit"], input[type="submit"]')
    page.wait_for_load_state("domcontentloaded")


def verify_on_detail_page(page, pk):
    page.goto(f"{BASE_URL}/beneficiaires/{pk}/")
    page.wait_for_load_state("domcontentloaded")
    body_text = page.evaluate("() => document.body.innerText")
    assert "1200.50" in body_text or "1200,50" in body_text, (
        f"rsa_prime_activite attendu 1200.50, absent de la page detail:\n{body_text[:500]}"
    )
    assert "1234.56" in body_text or "1234,56" in body_text, (
        "apl attendu 1234.56, absent de la page detail"
    )
    assert "2000" in body_text, "salaire attendu 2000, absent de la page detail"
    print("  OK: '1 200,50' -> 1200.50, '1,234.56' -> 1234.56, '2000' -> 2000")


def main():
    unique = uuid.uuid4().hex[:8]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Bug 1.2 — Parsing decimal tolerant:")
            pk = create_beneficiary(page, "E2E", f"DEC{unique}")
            submit_snapshot(page, pk)
            verify_on_detail_page(page, pk)
        finally:
            browser.close()

    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
