#!/usr/bin/env python
"""Bug 1.3 — Un seul snapshot financier par mois calendaire.

Cree deux interactions consecutives avec donnees financieres dans le meme
mois (le mois courant) et verifie qu'un seul snapshot existe pour ce mois,
et que ses valeurs correspondent a la derniere saisie.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal

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


def get_beneficiary_id():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rosa.settings")
    import django

    django.setup()
    from beneficiaries.models import Beneficiary

    b = Beneficiary.objects.first()
    assert b is not None
    return b.pk


def submit_interaction(page, pk, rsa):
    page.goto(f"{BASE_URL}/beneficiaires/{pk}/interactions/new/")
    page.wait_for_load_state("domcontentloaded")
    page.fill("#id_title", f"Test interaction {rsa}")
    page.fill("#id_description", "Snapshot upsert test")
    # Ouvrir la section financiere (cachee par defaut)
    page.evaluate("() => { document.getElementById('financial-section').style.display='block'; }")
    page.fill("#id_rsa_prime_activite", str(rsa))
    page.click('button[type="submit"]:has-text("Enregistrer")')
    page.wait_for_load_state("domcontentloaded")


def main():
    pk = get_beneficiary_id()

    # Pre-cleanup: supprimer tous les snapshots du mois courant pour partir clean
    from django.utils import timezone
    from beneficiaries.models import FinancialSnapshot, Interaction

    now = timezone.now()
    FinancialSnapshot.objects.filter(
        beneficiary_id=pk, date__year=now.year, date__month=now.month
    ).delete()
    Interaction.objects.filter(beneficiary_id=pk, title__startswith="Test interaction").delete()
    initial = FinancialSnapshot.objects.filter(beneficiary_id=pk).count()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            login(page)
            print("Bug 1.3 — Upsert mensuel snapshot via interaction:")
            submit_interaction(page, pk, 100)
            submit_interaction(page, pk, 250)
        finally:
            browser.close()

    snaps_this_month = FinancialSnapshot.objects.filter(
        beneficiary_id=pk, date__year=now.year, date__month=now.month
    )
    count = snaps_this_month.count()
    assert count == 1, f"Devrait avoir 1 snapshot ce mois, en a {count}"
    latest = snaps_this_month.first()
    assert latest.rsa_prime_activite == Decimal("250"), (
        f"rsa devrait etre 250 (derniere saisie), trouve {latest.rsa_prime_activite}"
    )
    print(f"  OK: 1 seul snapshot mensuel, valeur a jour (250). Total snapshots: {initial + 1}")

    # Cleanup
    snaps_this_month.delete()
    Interaction.objects.filter(beneficiary_id=pk, title__startswith="Test interaction").delete()
    print("Tous les tests OK")


if __name__ == "__main__":
    sys.exit(main() or 0)
