#!/usr/bin/env python
"""Amelioration 2.1 — Profil/alerte deplaces en fin de formulaire.

Verifie que les champs profile_tag et alert_level apparaissent APRES
first_name/last_name dans le DOM (donc plus haut dans la sequence visuelle
de remplissage).
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


def get_dom_position(page, selector):
    return page.evaluate(
        f"""(() => {{
            const el = document.querySelector('{selector}');
            if (!el) return -1;
            const all = [...document.querySelectorAll('input, select, textarea, button')];
            return all.indexOf(el);
        }})()"""
    )


def check_order(page, url):
    page.goto(url)
    page.wait_for_load_state("domcontentloaded")
    pos_first_name = get_dom_position(page, "#id_first_name")
    pos_profile = get_dom_position(page, "#id_profile_tag")
    pos_alert_first = get_dom_position(page, "#id_alert_level_0")
    assert pos_first_name >= 0, "first_name introuvable"
    assert pos_profile > pos_first_name, (
        f"profile_tag (pos {pos_profile}) doit etre apres first_name (pos {pos_first_name})"
    )
    assert pos_alert_first > pos_first_name, (
        f"alert_level (pos {pos_alert_first}) doit etre apres first_name (pos {pos_first_name})"
    )
    print(f"  OK {url}: first_name={pos_first_name}, profile_tag={pos_profile}, alert_level={pos_alert_first}")


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rosa.settings")
    import django

    django.setup()
    from beneficiaries.models import Beneficiary

    b = Beneficiary.objects.first()
    assert b is not None
    pk = b.pk

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Amelioration 2.1 — Ordre des champs:")
            check_order(page, f"{BASE_URL}/beneficiaires/new/")
            check_order(page, f"{BASE_URL}/beneficiaires/{pk}/edit/")
        finally:
            browser.close()

    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
