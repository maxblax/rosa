"""
Context processors pour rosa/LIEN
Rend les variables globales disponibles dans tous les templates
"""
from django.conf import settings


def association_info(request):
    """
    Expose les informations de l'association dans tous les templates
    """
    return {
        'ASSOCIATION_NAME': settings.ASSOCIATION_NAME,
        'ASSOCIATION_FULL_NAME': settings.ASSOCIATION_FULL_NAME,
    }
