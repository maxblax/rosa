#!/usr/bin/env python3
"""
Script pour créer un superuser admin pour ONA
"""

import os
import sys
import django

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ona.settings')
sys.path.append('/Users/max/Data/dev/ona')

django.setup()

from django.contrib.auth.models import User
from volunteers.models import Volunteer

def create_admin_user():
    """Crée un utilisateur admin et son profil bénévole"""

    # Vérifier si l'admin existe déjà
    if User.objects.filter(username='admin').exists():
        print("✅ L'utilisateur admin existe déjà")
        admin_user = User.objects.get(username='admin')
    else:
        # Créer le superuser
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@admin.com',
            password='admin',
            first_name='Administrateur',
            last_name='Système'
        )
        print("✅ Superuser admin créé avec succès")
        print("   Username: admin")
        print("   Email: admin@admin.com")
        print("   Password: admin")

    # Vérifier si le profil volunteer existe
    try:
        volunteer_profile = admin_user.volunteer_profile
        print("✅ Profil bénévole admin existe déjà")
    except Volunteer.DoesNotExist:
        # Créer le profil volunteer pour l'admin
        volunteer_profile = Volunteer.objects.create(
            user=admin_user,
            role='ADMIN',
            status='ACTIVE',
            skills='Administration système, gestion des utilisateurs',
            availability='Disponible selon les besoins',
        )
        print("✅ Profil bénévole admin créé avec succès")

    return admin_user

def create_demo_users():
    """Crée quelques utilisateurs de démonstration"""

    demo_users = [
        {
            'username': 'marie.orcel',
            'email': 'marie.orcel@apa30.org',
            'password': 'demo123',
            'first_name': 'Marie',
            'last_name': 'Orcel',
            'civility': 'MME',
            'role': 'EMPLOYEE',
            'skills': 'Accompagnement social, entretiens individuels',
            'availability': 'Lundi au vendredi 9h-17h'
        },
        {
            'username': 'jean.dupont',
            'email': 'jean.dupont@apa30.org',
            'password': 'demo123',
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'civility': 'M',
            'role': 'VOLUNTEER_INTERVIEW',
            'skills': 'Aide administrative, orientation des bénéficiaires',
            'availability': 'Mardi et jeudi après-midi'
        },
        {
            'username': 'pierre.martin',
            'email': 'pierre.martin@apa30.org',
            'password': 'demo123',
            'first_name': 'Pierre',
            'last_name': 'Martin',
            'civility': 'M',
            'role': 'VOLUNTEER_GOVERNANCE',
            'skills': 'Analyse financière, rapports statistiques',
            'availability': 'Premier samedi du mois'
        }
    ]

    for user_data in demo_users:
        # Vérifier si l'utilisateur existe déjà
        if User.objects.filter(username=user_data['username']).exists():
            print(f"⚠️ L'utilisateur {user_data['username']} existe déjà")
            continue

        # Créer l'utilisateur
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name']
        )

        # Créer le profil bénévole
        volunteer = Volunteer.objects.create(
            user=user,
            civility=user_data['civility'],
            role=user_data['role'],
            status='ACTIVE',
            skills=user_data['skills'],
            availability=user_data['availability']
        )

        print(f"✅ Utilisateur {user_data['username']} créé avec succès")

if __name__ == '__main__':
    print("🚀 Création des utilisateurs admin et démo...")
    print()

    # Créer l'admin
    admin_user = create_admin_user()
    print()

    # Créer les utilisateurs démo
    print("📝 Création des utilisateurs de démonstration...")
    create_demo_users()
    print()

    print("🎉 Terminé ! Vous pouvez maintenant vous connecter avec :")
    print()
    print("👤 ADMIN:")
    print("   Username: admin")
    print("   Password: admin")
    print()
    print("👤 DÉMO (Salarié):")
    print("   Username: marie.orcel")
    print("   Password: demo123")
    print()
    print("👤 DÉMO (Bénévole Entretien):")
    print("   Username: jean.dupont")
    print("   Password: demo123")
    print()
    print("👤 DÉMO (Bénévole Gouvernance):")
    print("   Username: pierre.martin")
    print("   Password: demo123")