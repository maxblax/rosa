from django import template
from beneficiaries.models import Beneficiary

register = template.Library()

@register.simple_tag
def get_beneficiaries():
    """Récupère tous les bénéficiaires actifs triés par nom"""
    return Beneficiary.objects.all().order_by('last_name', 'first_name')