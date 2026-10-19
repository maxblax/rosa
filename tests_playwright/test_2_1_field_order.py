#!/usr/bin/env python
"""Amelioration 2.1 — Profil/alerte deplaces en fin de formulaire.

Verifie que les champs profile_tag et alert_level apparaissent APRES
first_name/last_name dans le DOM (donc plus haut dans la sequence visuelle
de remplissage).
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


def create_beneficiary(page, first_name, last_name):
    page.goto(f"{BASE_URL}/beneficiaires/new/")
    page.wait_for_load_state("domcontentloaded")
    page.check("#id_gdpr_consent")
    page.fill("#id_first_name", first_name)
    page.fill("#id_last_name", last_name)
    page.click('button[type="submit"]:has-text("Créer")')
    page.wait_for_load_state("domcontentloaded")
    # URL finale: /beneficiaires/<pk>/
    parts = page.url.rstrip("/").split("/")
    return int(parts[-1])


def main():
    unique = uuid.uuid4().hex[:8]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Amelioration 2.1 — Ordre des champs:")
            pk = create_beneficiary(page, "E2E", f"TEST{unique}")
            check_order(page, f"{BASE_URL}/beneficiaires/new/")
            check_order(page, f"{BASE_URL}/beneficiaires/{pk}/edit/")
        finally:
            browser.close()

    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
