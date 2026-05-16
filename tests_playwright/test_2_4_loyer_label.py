#!/usr/bin/env python
"""Amelioration 2.4 — Clarification du label "Loyer residuel"."""
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
    from beneficiaries.models import Beneficiary

    b = Beneficiary.objects.first()
    pk = b.pk

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Amelioration 2.4 — Loyer libelle clair:")
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
