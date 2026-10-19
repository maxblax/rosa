#!/usr/bin/env python
"""Bug 1.3 — Un seul snapshot financier par mois calendaire.

Cree un beneficiaire frais puis deux interactions consecutives avec
donnees financieres dans le meme mois (le mois courant). Verifie, via la
fiche beneficiaire, qu'un seul snapshot existe pour ce mois (pas de section
"Historique" avec plusieurs entrees) et que la valeur affichee correspond a
la derniere saisie.
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


def submit_interaction(page, pk, title, rsa):
    page.goto(f"{BASE_URL}/beneficiaires/{pk}/interactions/new/")
    page.wait_for_load_state("domcontentloaded")
    page.fill("#id_title", title)
    page.fill("#id_description", "Snapshot upsert test")
    # Ouvrir la section financiere (cachee par defaut)
    page.evaluate("() => { document.getElementById('financial-section').style.display='block'; }")
    page.fill("#id_rsa_prime_activite", str(rsa))
    page.click('button[type="submit"]:has-text("Enregistrer")')
    page.wait_for_load_state("domcontentloaded")


def main():
    unique = uuid.uuid4().hex[:8]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Bug 1.3 — Upsert mensuel snapshot via interaction:")
            pk = create_beneficiary(page, "E2E", f"UPSERT{unique}")

            submit_interaction(page, pk, f"Test interaction 100 {unique}", 100)
            submit_interaction(page, pk, f"Test interaction 250 {unique}", 250)

            page.goto(f"{BASE_URL}/beneficiaires/{pk}/")
            page.wait_for_load_state("domcontentloaded")
            body_text = page.evaluate("() => document.body.innerText")

            assert "Historique des photos instantanées" not in body_text, (
                "Plusieurs snapshots ce mois: la section Historique ne devrait pas apparaitre"
            )
            assert "250" in body_text, "La derniere valeur saisie (250) devrait etre affichee"
            print("  OK: 1 seul snapshot mensuel (pas d'historique), valeur a jour (250)")
        finally:
            browser.close()

    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
