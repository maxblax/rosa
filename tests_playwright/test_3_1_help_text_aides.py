#!/usr/bin/env python
"""Section 3.1 — help_text/tooltips sur les acronymes d'aides."""
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
            print("Section 3.1 — Tooltips acronymes aides:")
            pk = create_beneficiary(page, "E2E", f"AIDES{unique}")

            page.goto(f"{BASE_URL}/beneficiaires/{pk}/snapshot/new/")
            page.wait_for_load_state("domcontentloaded")
            # Verifier presence de help_text pour quelques sigles cles
            info = page.evaluate(
                """() => {
                    const get = id => {
                        const label = document.querySelector(`label[for="${id}"]`);
                        if (!label) return null;
                        const wrap = label.closest('div');
                        const help = wrap.querySelector('p.text-xs');
                        const tooltip = label.querySelector('[title]');
                        return {
                            help: help ? help.textContent.trim() : null,
                            tooltipTitle: tooltip ? tooltip.getAttribute('title') : null,
                        };
                    };
                    return {
                        rsa: get('id_rsa_prime_activite'),
                        cf: get('id_cf'),
                        asf: get('id_asf'),
                        css: get('id_css'),
                        loyer: get('id_loyer_residuel'),
                    };
                }"""
            )
            for code, expected in [
                ('rsa', 'CAF'),
                ('cf', '3 enfants'),
                ('asf', 'pension'),
                ('css', 'CMU'),
                ('loyer', 'APL'),
            ]:
                d = info[code]
                assert d and d['help'] and expected in d['help'], (
                    f"{code}: help_text manquant ou ne contient pas {expected!r}: {d}"
                )
                assert d['tooltipTitle'] == d['help'], (
                    f"{code}: tooltip title manquant"
                )
            print("  OK: RSA, CF, ASF, CSS, Loyer ont tous help_text + tooltip title")
        finally:
            browser.close()

    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
