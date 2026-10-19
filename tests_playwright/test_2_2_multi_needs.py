#!/usr/bin/env python
"""Amelioration 2.2 — Selection multiple des besoins exprimes.

Cree un beneficiaire, cree une interaction en cochant Alimentaire +
Vestimentaire, soumet, et verifie sur la page detail de l'interaction que
les deux besoins sont bien affiches.
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
    title = f"Test multi-needs {unique}"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Amelioration 2.2 — Selection multiple besoins:")
            pk = create_beneficiary(page, "E2E", f"NEEDS{unique}")

            page.goto(f"{BASE_URL}/beneficiaires/{pk}/interactions/new/")
            page.wait_for_load_state("domcontentloaded")
            page.fill("#id_title", title)
            page.fill("#id_description", "Multi needs test")
            # Cocher ALIMENTAIRE + VESTIMENTAIRE
            page.check('input[name="primary_need"][value="ALIMENTAIRE"]')
            page.check('input[name="primary_need"][value="VESTIMENTAIRE"]')
            page.click('button[type="submit"]:has-text("Enregistrer")')
            page.wait_for_load_state("domcontentloaded")

            # On atterrit sur la fiche beneficiaire, retrouver le lien de
            # l'interaction nouvellement creee et aller sur sa page detail.
            page.goto(f"{BASE_URL}/beneficiaires/{pk}/")
            page.wait_for_load_state("domcontentloaded")
            page.click(f'a:has-text("{title}")')
            page.wait_for_load_state("domcontentloaded")

            labels_text = page.evaluate(
                """() => {
                    const el = document.querySelector('body');
                    return el ? el.innerText : '';
                }"""
            )
            assert "Alimentaire" in labels_text, "Label 'Alimentaire' absent de la page detail"
            assert "Vestimentaire" in labels_text, "Label 'Vestimentaire' absent de la page detail"
            print("  OK: Alimentaire et Vestimentaire affiches sur la fiche interaction")
        finally:
            browser.close()

    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
