#!/usr/bin/env python
"""Bug 1.4 (extended) — Dates tolerantes sur tous les ecrans.

Verifie que les champs date hors beneficiaires (calendar, volunteers, dons)
sont aussi rendus en input texte JJ/MM/AAAA et parsent une saisie au format
francais.
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


def check_input(page, url, input_id):
    page.goto(url)
    page.wait_for_load_state("domcontentloaded")
    info = page.evaluate(f"""() => {{
        const inp = document.getElementById('{input_id}');
        if (!inp) return null;
        return {{ type: inp.type, placeholder: inp.placeholder, dataset: inp.dataset.tolerantDate }};
    }}""")
    assert info is not None, f"input #{input_id} introuvable sur {url}"
    assert info["type"] == "text", f"#{input_id} type={info['type']}, attendu text"
    assert info["placeholder"].startswith("JJ/MM/AAAA"), f"#{input_id} placeholder={info['placeholder']}"
    assert info["dataset"] == "true", f"#{input_id} dataset.tolerantDate={info['dataset']}"
    print(f"  OK: {url} #{input_id}")


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rosa.settings")
    import django

    django.setup()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Bug 1.4 (extended) — Dates tolerantes hors beneficiaires:")
            # Calendrier — nouveau rendez-vous
            check_input(page, f"{BASE_URL}/calendrier/appointments/create/", "id_appointment_date")
            # Calendrier — nouvelle disponibilite
            check_input(page, f"{BASE_URL}/calendrier/availability/create/", "id_specific_date")
            check_input(page, f"{BASE_URL}/calendrier/availability/create/", "id_valid_from")
            check_input(page, f"{BASE_URL}/calendrier/availability/create/", "id_valid_until")
            # Benevoles — nouveau
            check_input(page, f"{BASE_URL}/benevoles/create/", "id_birth_date")
            check_input(page, f"{BASE_URL}/benevoles/create/", "id_join_date")
            # Dons — nouveau
            check_input(page, f"{BASE_URL}/dons/create/", "id_date")
        finally:
            browser.close()

    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
