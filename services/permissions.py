"""Contrôles d'accès du module services, vérifiés avant l'exécution de la vue."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


def _profile(user):
    return getattr(user, 'volunteer_profile', None)


def can_use_services(user):
    """Bénévoles d'entretien, salariés, administrateurs : inscrire, demander, pointer."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    profile = _profile(user)
    return bool(profile and profile.can_modify_beneficiaries)


def is_services_admin(user):
    """Administrateurs et salariés : listes, validation des aides, versements, catalogue."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    profile = _profile(user)
    return bool(profile and profile.can_manage_users)


class ServicesAccessMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not can_use_services(request.user):
            messages.error(request, "Vous n'avez pas accès aux services aux bénéficiaires.")
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class ServicesAdminMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not is_services_admin(request.user):
            messages.error(request, 'Cette action est réservée aux administrateurs et salariés.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
