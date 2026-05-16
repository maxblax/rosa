#!/usr/bin/env python
"""Amelioration 2.5 — Disponibilites recurrentes sans date de fin.

Crée un creneau weekly avec la case "Sans date de fin" cochee, soumet,
verifie que valid_until est NULL en base.
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


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rosa.settings")
    import django

    django.setup()
    from calendar_app.models import AvailabilitySlot, VolunteerCalendar

    vc = VolunteerCalendar.objects.first()
    assert vc is not None, "Need a VolunteerCalendar to test"
    AvailabilitySlot.objects.filter(title="Test sans fin").delete()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Amelioration 2.5 — Disponibilites sans date de fin:")
            page.goto(f"{BASE_URL}/calendrier/availability/create/")
            page.wait_for_load_state("domcontentloaded")
            # volunteer_calendar est un input hidden alimente par un widget custom.
            page.evaluate(
                f"() => {{ document.getElementById('id_volunteer_calendar').value = '{vc.pk}'; }}"
            )
            page.fill('input[name="title"]', "Test sans fin")
            page.select_option('select[name="recurrence_type"]', "WEEKLY")
            page.select_option('select[name="weekday"]', "1")  # Mardi
            page.fill('input[name="start_time"]', "09:00")
            page.fill('input[name="end_time"]', "12:00")
            # valid_from = today, en JJ/MM/AAAA
            from datetime import date

            page.fill('input[name="valid_from"]', date.today().strftime("%d/%m/%Y"))
            # Cocher sans date de fin (devrait deja l'etre par defaut)
            page.check("#no-end-date-checkbox")
            page.click('button[type="submit"]')
            page.wait_for_load_state("domcontentloaded")
        finally:
            browser.close()

    slot = AvailabilitySlot.objects.filter(title="Test sans fin").first()
    assert slot is not None, "Slot non cree"
    assert slot.valid_until is None, f"valid_until devrait etre None, got {slot.valid_until}"
    print(f"  OK: slot weekly cree, valid_until = NULL")
    slot.delete()
    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
