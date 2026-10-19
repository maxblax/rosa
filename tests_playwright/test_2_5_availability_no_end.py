#!/usr/bin/env python
"""Amelioration 2.5 — Disponibilites recurrentes sans date de fin.

Cree un creneau weekly avec la case "Sans date de fin" cochee, soumet, puis
verifie sur la page d'edition du creneau que le champ valid_until est bien
vide (donc NULL en base).
"""
import os
import sys
import uuid
from datetime import date

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


def main():
    unique = uuid.uuid4().hex[:8]
    title = f"Test sans fin {unique}"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Amelioration 2.5 — Disponibilites sans date de fin:")
            page.goto(f"{BASE_URL}/calendrier/availability/create/")
            page.wait_for_load_state("domcontentloaded")
            # volunteer_calendar est pre-rempli et force cote serveur sur le
            # calendrier de l'utilisateur connecte (superuser -> calendrier
            # auto-cree), pas besoin de le renseigner depuis le navigateur.
            page.fill('input[name="title"]', title)
            page.select_option('select[name="recurrence_type"]', "WEEKLY")
            page.select_option('select[name="weekday"]', "1")  # Mardi
            page.fill('input[name="start_time"]', "09:00")
            page.fill('input[name="end_time"]', "12:00")
            # valid_from = today, en JJ/MM/AAAA
            page.fill('input[name="valid_from"]', date.today().strftime("%d/%m/%Y"))
            # Cocher sans date de fin (devrait deja l'etre par defaut)
            page.check("#no-end-date-checkbox")
            page.click('button[type="submit"]')
            page.wait_for_load_state("domcontentloaded")

            # Retrouver le creneau cree dans la liste et ouvrir son edition
            page.goto(f"{BASE_URL}/calendrier/availability/")
            page.wait_for_load_state("domcontentloaded")
            row = page.locator(f"tr:has-text('{title}')")
            row.locator('a:has-text("Modifier")').click()
            page.wait_for_load_state("domcontentloaded")

            valid_until_value = page.input_value('input[name="valid_until"]')
            assert valid_until_value == "", (
                f"valid_until devrait etre vide, got {valid_until_value!r}"
            )
            print("  OK: slot weekly cree, valid_until vide (NULL)")
        finally:
            browser.close()

    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
