#!/usr/bin/env python
"""Section 3.2 — Bouton Editer sur les interactions de la fiche beneficiaire."""
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


def create_interaction(page, pk, title):
    page.goto(f"{BASE_URL}/beneficiaires/{pk}/interactions/new/")
    page.wait_for_load_state("domcontentloaded")
    page.fill("#id_title", title)
    page.fill("#id_description", "Test edit button")
    page.click('button[type="submit"]:has-text("Enregistrer")')
    page.wait_for_load_state("domcontentloaded")


def main():
    unique = uuid.uuid4().hex[:8]
    title = f"Interaction pour test edit {unique}"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Section 3.2 — Bouton Editer interactions:")
            pk = create_beneficiary(page, "E2E", f"EDIT{unique}")
            create_interaction(page, pk, title)

            page.goto(f"{BASE_URL}/beneficiaires/{pk}/")
            page.wait_for_load_state("domcontentloaded")

            # Le bouton Editer doit etre present pour notre interaction
            row = page.locator(f"#interaction-history div:has-text('{title}')").first
            edit_link = row.locator('a:has-text("Éditer")')
            href = edit_link.get_attribute("href")
            assert href and f"/beneficiaires/{pk}/interactions/" in href and href.endswith("/edit/"), (
                f"Bouton Editer absent ou href inattendu: {href!r}"
            )
            print(f"  OK: bouton Editer present (href {href})")

            # Cliquer dessus et verifier qu'on atterrit sur la page d'edition
            edit_link.click()
            page.wait_for_url(f"**{href}")
            print("  OK: navigation vers la page edit fonctionne")
        finally:
            browser.close()

    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
