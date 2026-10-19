#!/usr/bin/env python
"""Amelioration 2.4 — Clarification du label "Loyer residuel"."""
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

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Amelioration 2.4 — Loyer libelle clair:")
            pk = create_beneficiary(page, "E2E", f"LOYER{unique}")

            page.goto(f"{BASE_URL}/beneficiaires/{pk}/snapshot/new/")
            page.wait_for_load_state("domcontentloaded")
            info = page.evaluate(
                """() => {
                    const inp = document.getElementById('id_loyer_residuel');
                    const label = document.querySelector('label[for="id_loyer_residuel"]');
                    const wrapper = label.closest('div');
                    const help = wrapper.querySelector('p.text-xs');
                    return {
                        label: label.textContent.trim(),
                        help: help ? help.textContent.trim() : null,
                    };
                }"""
            )
            assert "Loyer" in info["label"] and "total" in info["label"].lower(), (
                f"Label inattendu: {info['label']!r}"
            )
            assert info["help"] and "APL" in info["help"], f"help_text manquant ou incorrect: {info['help']!r}"
            print(f"  OK: label={info['label']!r}, help mentionne APL")
        finally:
            browser.close()

    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
