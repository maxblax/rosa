#!/usr/bin/env python
"""Bug 1.1 — La touche Entrée ne doit pas valider/soumettre les formulaires POST.

Les formulaires GET (recherche/filtre) doivent rester soumettables avec Entrée.
"""
import sys
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


def test_enter_does_not_submit_post_form(page):
    page.goto(f"{BASE_URL}/beneficiaires/new/")
    page.wait_for_load_state("domcontentloaded")
    page.evaluate(
        """() => {
            window.__submitCount = 0;
            document.querySelector('form').addEventListener('submit', (e) => {
                window.__submitCount++; e.preventDefault();
            }, true);
            document.getElementById('id_gdpr_consent').checked = true;
            document.getElementById('id_last_name').value = 'TEST';
            document.getElementById('id_first_name').focus();
            document.getElementById('id_first_name').value = 'Prenom';
        }"""
    )
    page.keyboard.press("Enter")
    count = page.evaluate("() => window.__submitCount")
    assert count == 0, f"Enter should not submit POST form, got submitCount={count}"
    print("  OK: Enter ne soumet pas le formulaire POST")


def test_enter_still_submits_get_search_form(page):
    page.goto(f"{BASE_URL}/beneficiaires/")
    page.wait_for_load_state("domcontentloaded")
    page.evaluate(
        """() => {
            window.__submitCount = 0;
            const input = document.querySelector('input[name=\"search\"]');
            input.form.addEventListener('submit', (e) => {
                window.__submitCount++; e.preventDefault();
            }, true);
            input.focus(); input.value = 'X';
        }"""
    )
    page.keyboard.press("Enter")
    count = page.evaluate("() => window.__submitCount")
    assert count == 1, f"Enter should submit GET search form, got submitCount={count}"
    print("  OK: Enter soumet bien le formulaire GET de recherche")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Bug 1.1 — Validation par Entree:")
            test_enter_does_not_submit_post_form(page)
            test_enter_still_submits_get_search_form(page)
            print("Tous les tests OK")
        finally:
            browser.close()


if __name__ == "__main__":
    sys.exit(main() or 0)
