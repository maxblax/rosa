#!/usr/bin/env python
"""Script pour créer les données de test nécessaires"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rosa.settings')
django.setup()

from django.contrib.auth.models import User
from volunteers.models import Volunteer

# Créer un profil Volunteer pour l'admin
admin = User.objects.get(username='admin')

# Vérifier si le profil existe déjà
if not hasattr(admin, 'volunteer_profile') or admin.volunteer_profile is None:
    volunteer = Volunteer.objects.create(
        user=admin,
        role='ADMIN',
        phone='0601020304'
    )
    print(f"✅ Profil Volunteer créé pour {admin.username}")
else:
    print(f"✅ Profil Volunteer déjà existant pour {admin.username}")

print("✅ Configuration terminée")
