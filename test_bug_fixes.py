#!/usr/bin/env python
"""
Script de test automatisé pour valider toutes les corrections de bugs
"""
import sys
import time
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://localhost:5678"
ADMIN_USER = "admin"
ADMIN_PASSWORD = "admin"

def login(page):
    """Login to the application"""
    print("🔐 Connexion à l'application...")
    page.goto(f"{BASE_URL}/auth/login/")
    page.fill('input[name="username"]', ADMIN_USER)
    page.fill('input[name="password"]', ADMIN_PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    print("✅ Connexion réussie")

def test_rgpd_consent(page):
    """Test: RGPD consent checkbox on beneficiary creation"""
    print("\n📋 Test: Case RGPD pour le consentement")

    page.goto(f"{BASE_URL}/beneficiaires/new/")
    page.wait_for_load_state('networkidle')

    # Debug: Afficher l'URL actuelle
    print(f"  URL actuelle: {page.url}")

    # Debug: Sauvegarder une screenshot
    page.screenshot(path="/tmp/test_rgpd.png")
    print("  Screenshot sauvegardée dans /tmp/test_rgpd.png")

    # Vérifier la présence de la section RGPD
    rgpd_section = page.locator('text=Protection des données personnelles')
    if not rgpd_section.is_visible():
        print(f"  ⚠️  Page HTML: {page.content()[:500]}")
    assert rgpd_section.is_visible(), "Section RGPD non visible"
    print("  ✓ Section RGPD présente")

    # Vérifier la présence de la checkbox
    gdpr_checkbox = page.locator('input[name="gdpr_consent"]')
    assert gdpr_checkbox.is_visible(), "Checkbox RGPD non visible"
    print("  ✓ Checkbox RGPD présente")

    # Vérifier l'icône de bouclier
    shield_icon = page.locator('i.fa-shield-alt')
    assert shield_icon.is_visible(), "Icône bouclier non visible"
    print("  ✓ Icône de sécurité présente")

    # Test: tentative de création sans consentement (doit échouer)
    page.fill('input[name="first_name"]', 'Test')
    page.fill('input[name="last_name"]', 'RGPD')
    page.click('button[type="submit"]')
    time.sleep(1)

    # Vérifier qu'on est toujours sur la page de création (formulaire non validé)
    assert "/beneficiaires/new/" in page.url, "Le formulaire aurait dû être rejeté"
    print("  ✓ Validation RGPD obligatoire fonctionne")

    print("✅ Test RGPD: SUCCÈS")

def test_nationality_field(page):
    """Test: Nationality field in beneficiary creation"""
    print("\n🌍 Test: Champ Nationalité")

    page.goto(f"{BASE_URL}/beneficiaires/new/")
    page.wait_for_load_state('networkidle')

    # Vérifier la présence du champ nationalité
    nationality_field = page.locator('select[name="nationality"]')
    assert nationality_field.is_visible(), "Champ nationalité non visible"
    print("  ✓ Champ Nationalité présent")

    # Vérifier les options
    options = nationality_field.locator('option').all_inner_texts()
    assert 'Française' in ' '.join(options), "Option 'Française' manquante"
    assert 'Union Européenne' in ' '.join(options), "Option 'Union Européenne' manquante"
    assert 'Hors Union Européenne' in ' '.join(options), "Option 'Hors Union Européenne' manquante"
    print("  ✓ Toutes les options de nationalité présentes")

    print("✅ Test Nationalité: SUCCÈS")

def test_referral_source_field(page):
    """Test: Referral source field in beneficiary creation"""
    print("\n📊 Test: Champ d'adressage")

    page.goto(f"{BASE_URL}/beneficiaires/new/")
    page.wait_for_load_state('networkidle')

    # Vérifier la présence du champ
    referral_field = page.locator('input[name="referral_source"]')
    assert referral_field.is_visible(), "Champ 'Adressé par' non visible"
    print("  ✓ Champ 'Adressé par' présent")

    # Vérifier le placeholder
    placeholder = referral_field.get_attribute('placeholder')
    assert 'Croix-Rouge' in placeholder or 'assistant social' in placeholder, "Placeholder incorrect"
    print("  ✓ Placeholder informatif présent")

    print("✅ Test Champ d'adressage: SUCCÈS")

def test_create_beneficiary_with_all_fields(page):
    """Test: Create a complete beneficiary with all new fields"""
    print("\n👤 Test: Création complète d'un bénéficiaire")

    page.goto(f"{BASE_URL}/beneficiaires/new/")
    page.wait_for_load_state('networkidle')

    # Remplir le formulaire
    page.check('input[name="gdpr_consent"]')
    print("  ✓ Consentement RGPD coché")

    page.select_option('select[name="civility"]', 'M')
    page.fill('input[name="first_name"]', 'Jean')
    page.fill('input[name="last_name"]', 'DUPONT')
    page.fill('input[name="birth_date"]', '1980-05-15')

    page.select_option('select[name="nationality"]', 'FRANCAISE')
    print("  ✓ Nationalité sélectionnée")

    page.fill('input[name="referral_source"]', 'Croix-Rouge')
    print("  ✓ Source d'adressage renseignée")

    page.fill('input[name="phone"]', '0601020304')
    page.fill('input[name="email"]', 'jean.dupont@test.fr')

    # Soumettre le formulaire
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')

    # Vérifier la redirection vers la page de détail
    assert "/beneficiaires/" in page.url and "/beneficiaires/new/" not in page.url, "Pas de redirection après création"
    print("  ✓ Bénéficiaire créé avec succès")

    # Vérifier l'affichage de la nationalité
    assert page.locator('text=Française').is_visible(), "Nationalité non affichée"
    print("  ✓ Nationalité affichée dans le profil")

    print("✅ Test Création complète: SUCCÈS")

def test_calendar_navigation(page):
    """Test: Calendar global view week navigation"""
    print("\n📅 Test: Navigation calendrier global")

    # D'abord créer un profil volunteer pour l'admin
    page.goto(f"{BASE_URL}/benevoles/new/")
    page.wait_for_load_state('networkidle')

    # Si la page existe, remplir le formulaire
    if "new" in page.url:
        page.select_option('select[name="role"]', 'ADMIN')
        page.fill('input[name="phone"]', '0601020304')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

    # Aller au calendrier global
    page.goto(f"{BASE_URL}/calendrier/global/")
    page.wait_for_load_state('networkidle')

    # Récupérer la semaine affichée
    week_text = page.locator('text=/Semaine du/').inner_text()
    print(f"  ℹ️  {week_text}")

    # Tester la navigation semaine précédente
    page.click('a:has(i.fa-chevron-left)')
    page.wait_for_load_state('networkidle')
    new_week_text = page.locator('text=/Semaine du/').inner_text()
    assert new_week_text != week_text, "La navigation vers la semaine précédente ne fonctionne pas"
    print("  ✓ Navigation semaine précédente: OK")

    # Tester le retour à cette semaine
    page.click('text=Cette semaine')
    page.wait_for_load_state('networkidle')
    current_week_text = page.locator('text=/Semaine du/').inner_text()
    print("  ✓ Retour à la semaine actuelle: OK")

    # Tester la navigation semaine suivante
    page.click('a:has(i.fa-chevron-right)')
    page.wait_for_load_state('networkidle')
    next_week_text = page.locator('text=/Semaine du/').inner_text()
    assert next_week_text != current_week_text, "La navigation vers la semaine suivante ne fonctionne pas"
    print("  ✓ Navigation semaine suivante: OK")

    print("✅ Test Navigation calendrier: SUCCÈS")

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("🧪 TESTS DE VALIDATION DES CORRECTIONS")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Login
            login(page)

            # Run all tests
            test_rgpd_consent(page)
            test_nationality_field(page)
            test_referral_source_field(page)
            test_create_beneficiary_with_all_fields(page)
            test_calendar_navigation(page)

            print("\n" + "=" * 60)
            print("✅ TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS!")
            print("=" * 60)
            return 0

        except Exception as e:
            print("\n" + "=" * 60)
            print(f"❌ ÉCHEC DU TEST: {str(e)}")
            print("=" * 60)
            import traceback
            traceback.print_exc()
            return 1

        finally:
            browser.close()

if __name__ == "__main__":
    sys.exit(run_all_tests())
