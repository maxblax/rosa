"""
Système de permissions RBAC (Role-Based Access Control) pour ONA
Hiérarchie des rôles:
- ADMIN > EMPLOYEE > (VOLUNTEER_INTERVIEW & VOLUNTEER_GOVERNANCE)
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin


class VolunteerRequiredMixin(LoginRequiredMixin):
    """Vérifie que l'utilisateur a un profil bénévole"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not hasattr(request.user, 'volunteer_profile'):
            messages.error(
                request,
                'Vous devez avoir un profil bénévole pour accéder à cette page.'
            )
            return redirect('home')

        return super().dispatch(request, *args, **kwargs)


class CanModifyBeneficiariesMixin(VolunteerRequiredMixin):
    """
    Restreint l'accès aux bénévoles qui peuvent modifier les bénéficiaires
    Autorisés: ADMIN, EMPLOYEE, VOLUNTEER_INTERVIEW
    Refusés: VOLUNTEER_GOVERNANCE
    """

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        # Si super() a déjà redirigé (pas de profil), on retourne la réponse
        if response.status_code == 302:
            return response

        volunteer = request.user.volunteer_profile

        if not volunteer.can_modify_beneficiaries:
            messages.error(
                request,
                'Vous n\'avez pas accès à cette section. '
                'Seuls les bénévoles d\'entretien, salariés et administrateurs peuvent gérer les bénéficiaires.'
            )
            return redirect('home')

        return response


class CanAccessCalendarMixin(VolunteerRequiredMixin):
    """
    Restreint l'accès au calendrier
    Autorisés: ADMIN, EMPLOYEE, VOLUNTEER_INTERVIEW
    Refusés: VOLUNTEER_GOVERNANCE
    """

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        if response.status_code == 302:
            return response

        volunteer = request.user.volunteer_profile

        # Les bénévoles de gouvernance ne peuvent pas accéder au calendrier
        if volunteer.role == 'VOLUNTEER_GOVERNANCE':
            messages.error(
                request,
                'Vous n\'avez pas accès au calendrier. '
                'Cette fonctionnalité est réservée aux bénévoles d\'entretien, salariés et administrateurs.'
            )
            return redirect('home')

        return response


class AdminOrEmployeeRequiredMixin(VolunteerRequiredMixin):
    """Restreint l'accès aux ADMIN et EMPLOYEE uniquement"""

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        if response.status_code == 302:
            return response

        volunteer = request.user.volunteer_profile

        if not volunteer.can_manage_users:
            messages.error(
                request,
                'Vous n\'avez pas les permissions nécessaires pour effectuer cette action. '
                'Seuls les administrateurs et salariés peuvent gérer les utilisateurs.'
            )
            return redirect('volunteers:list')

        return response


class CanEditVolunteerMixin(VolunteerRequiredMixin):
    """
    Permet aux utilisateurs de modifier leur propre profil
    ou pour ADMIN/EMPLOYEE de modifier n'importe quel profil
    """

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        if response.status_code == 302:
            return response

        volunteer = request.user.volunteer_profile
        volunteer_to_edit = self.get_object()

        # ADMIN et EMPLOYEE peuvent modifier n'importe quel profil
        if volunteer.can_manage_users:
            return response

        # Les autres peuvent seulement modifier leur propre profil
        if volunteer == volunteer_to_edit:
            return response

        messages.error(
            request,
            'Vous n\'avez pas les permissions nécessaires pour modifier ce profil. '
            'Vous pouvez uniquement modifier votre propre profil.'
        )
        return redirect('volunteers:detail', pk=volunteer.pk)

    def get_object(self):
        """Permet de récupérer l'objet avant dispatch"""
        if not hasattr(self, 'object') or self.object is None:
            self.object = super().get_object()
        return self.object


class CanAccessAnalysisMixin(VolunteerRequiredMixin):
    """
    Restreint l'accès aux analyses
    Autorisés: ADMIN, EMPLOYEE, VOLUNTEER_GOVERNANCE
    Refusés: VOLUNTEER_INTERVIEW
    """

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        if response.status_code == 302:
            return response

        volunteer = request.user.volunteer_profile

        if not volunteer.can_access_analysis:
            messages.error(
                request,
                'Vous n\'avez pas accès aux analyses. '
                'Cette fonctionnalité est réservée aux bénévoles de gouvernance, salariés et administrateurs.'
            )
            return redirect('home')

        return response
