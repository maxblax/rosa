from .models import FinancialAidRequest
from .permissions import is_services_admin


def services_badges(request):
    """Compteur des demandes d'aide à traiter, affiché dans la navigation des admins."""
    user = getattr(request, 'user', None)
    if not user or not is_services_admin(user):
        return {}
    return {'pending_aid_count': FinancialAidRequest.objects.filter(
        status=FinancialAidRequest.STATUS_PENDING).count()}
