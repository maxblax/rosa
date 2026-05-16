#!/usr/bin/env python
"""Section 3.2 — Bouton Editer sur les interactions de la fiche beneficiaire."""
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
    from beneficiaries.models import Beneficiary, Interaction

    b = Beneficiary.objects.first()
    pk = b.pk

    # S'assurer qu'au moins une interaction existe.
    inter, created = Interaction.objects.get_or_create(
        beneficiary_id=pk,
        title="Interaction pour test edit",
        defaults={"interaction_type": "ASSOCIATION", "description": "Test"},
    )
    ipk = inter.pk

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Section 3.2 — Bouton Editer interactions:")
            page.goto(f"{BASE_URL}/beneficiaires/{pk}/")
            page.wait_for_load_state("domcontentloaded")
            # Le bouton Editer doit etre present pour notre interaction
            expected_url = f"/beneficiaires/{pk}/interactions/{ipk}/edit/"
            found = page.evaluate(
                f"() => !!document.querySelector('a[href=\"{expected_url}\"]')"
            )
            assert found, f"Bouton Editer absent pour l'interaction {ipk}"
            print(f"  OK: bouton Editer present (href {expected_url})")
            # Cliquer dessus et verifier qu'on atterrit sur la page d'edition
            page.click(f'a[href="{expected_url}"]')
            page.wait_for_url(f"**{expected_url}")
            print(f"  OK: navigation vers la page edit fonctionne")
        finally:
            browser.close()

    if created:
        Interaction.objects.filter(pk=ipk).delete()
    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
