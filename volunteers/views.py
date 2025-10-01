from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponseForbidden
from django.db import transaction
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, date
from .models import Volunteer
from .forms import VolunteerForm


class AdminOrEmployeeRequiredMixin:
    """Mixin pour restreindre l'accès aux ADMIN et EMPLOYEE uniquement"""

    def dispatch(self, request, *args, **kwargs):
        # Vérifier si l'utilisateur a un profil bénévole
        if not hasattr(request.user, 'volunteer_profile'):
            messages.error(request, 'Vous devez avoir un profil bénévole pour accéder à cette page.')
            return redirect('volunteers:list')

        volunteer = request.user.volunteer_profile

        # Seuls les ADMIN et EMPLOYEE peuvent gérer les utilisateurs
        if volunteer.role not in ['ADMIN', 'EMPLOYEE']:
            messages.error(
                request,
                'Vous n\'avez pas les permissions nécessaires pour effectuer cette action. '
                'Seuls les administrateurs et salariés peuvent gérer les utilisateurs.'
            )
            return redirect('volunteers:list')

        return super().dispatch(request, *args, **kwargs)


class CanEditVolunteerMixin:
    """Mixin pour permettre aux utilisateurs de modifier leur propre profil ou pour ADMIN/EMPLOYEE de modifier n'importe quel profil"""

    def dispatch(self, request, *args, **kwargs):
        # Vérifier si l'utilisateur a un profil bénévole
        if not hasattr(request.user, 'volunteer_profile'):
            messages.error(request, 'Vous devez avoir un profil bénévole pour accéder à cette page.')
            return redirect('volunteers:list')

        volunteer = request.user.volunteer_profile

        # Récupérer le bénévole à modifier
        volunteer_to_edit = self.get_object()

        # ADMIN et EMPLOYEE peuvent modifier n'importe quel profil
        if volunteer.role in ['ADMIN', 'EMPLOYEE']:
            return super().dispatch(request, *args, **kwargs)

        # Les autres peuvent seulement modifier leur propre profil
        if volunteer == volunteer_to_edit:
            return super().dispatch(request, *args, **kwargs)

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


class VolunteerListView(LoginRequiredMixin, ListView):
    """Vue liste des bénévoles avec recherche et filtres par rôle"""
    model = Volunteer
    template_name = 'volunteers/list.html'
    context_object_name = 'volunteers'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('user')
        search_query = self.request.GET.get('search', '')
        role_filter = self.request.GET.get('role', '')
        status_filter = self.request.GET.get('status', '')

        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(phone__icontains=search_query)
            )

        if role_filter:
            queryset = queryset.filter(role=role_filter)

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['role_filter'] = self.request.GET.get('role', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['role_choices'] = Volunteer.ROLE_CHOICES
        context['status_choices'] = Volunteer.STATUS_CHOICES
        return context


class VolunteerCreateView(LoginRequiredMixin, AdminOrEmployeeRequiredMixin, CreateView):
    """Vue de création d'un nouveau bénévole"""
    model = Volunteer
    form_class = VolunteerForm
    template_name = 'volunteers/create.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_edit'] = False
        return kwargs

    def form_valid(self, form):
        with transaction.atomic():
            # Créer l'utilisateur Django
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )

            # Sauvegarder le bénévole
            self.object = form.save(commit=False)
            self.object.user = user
            self.object.save()

            messages.success(
                self.request,
                f'Bénévole {self.object.full_name} créé avec succès.'
            )

            return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('volunteers:detail', kwargs={'pk': self.object.pk})


class VolunteerDetailView(LoginRequiredMixin, DetailView):
    """Vue détail d'un bénévole avec statistiques des rendez-vous et disponibilités"""
    model = Volunteer
    template_name = 'volunteers/detail.html'
    context_object_name = 'volunteer'

    def get_context_data(self, **kwargs):
        from calendar_app.models import Appointment, AvailabilitySlot
        from collections import defaultdict
        from dateutil.relativedelta import relativedelta

        context = super().get_context_data(**kwargs)

        # Calculer les 12 derniers mois
        today = date.today()
        start_date = today - relativedelta(months=11)
        start_date = start_date.replace(day=1)

        # Récupérer le calendrier du bénévole
        if hasattr(self.object, 'calendar'):
            calendar = self.object.calendar

            # Statistiques par mois
            monthly_stats = []

            for i in range(12):
                month_date = start_date + relativedelta(months=i)
                next_month = month_date + relativedelta(months=1)

                # Compter les rendez-vous pour ce mois
                appointments_count = Appointment.objects.filter(
                    volunteer_calendar=calendar,
                    appointment_date__gte=month_date,
                    appointment_date__lt=next_month,
                    status__in=['SCHEDULED', 'CONFIRMED', 'COMPLETED']
                ).count()

                # Calculer les heures de disponibilité pour ce mois
                availability_slots = AvailabilitySlot.objects.filter(
                    volunteer_calendar=calendar,
                    slot_type='AVAILABILITY',
                    is_active=True
                )

                total_hours = 0
                for slot in availability_slots:
                    # Obtenir les occurrences dans ce mois
                    occurrences = slot.get_occurrences_in_range(month_date, next_month - relativedelta(days=1))
                    for occurrence in occurrences:
                        total_hours += slot.duration_hours

                monthly_stats.append({
                    'month': month_date,
                    'month_name': month_date.strftime('%B %Y'),
                    'appointments_count': appointments_count,
                    'availability_hours': round(total_hours, 1),
                })

            context['monthly_stats'] = list(reversed(monthly_stats))

            # Statistiques annuelles
            current_year = today.year
            year_start = date(current_year, 1, 1)
            year_appointments = Appointment.objects.filter(
                volunteer_calendar=calendar,
                appointment_date__gte=year_start,
                appointment_date__lte=today,
                status__in=['SCHEDULED', 'CONFIRMED', 'COMPLETED']
            )
            context['total_appointments_this_year'] = year_appointments.count()

            # Calculer les heures totales de RDV cette année
            total_hours_appointments = sum(a.duration_hours for a in year_appointments)
            context['total_hours_appointments_this_year'] = round(total_hours_appointments, 1)
        else:
            context['monthly_stats'] = []
            context['total_appointments_this_year'] = 0
            context['total_hours_appointments_this_year'] = 0

        # Nombre de bénéficiaires dont ce bénévole est l'interlocuteur privilégié
        context['preferred_beneficiaries_count'] = self.object.preferred_beneficiaries.count()

        return context


class VolunteerUpdateView(LoginRequiredMixin, CanEditVolunteerMixin, UpdateView):
    """Vue d'édition d'un bénévole"""
    model = Volunteer
    form_class = VolunteerForm
    template_name = 'volunteers/edit.html'
    context_object_name = 'volunteer'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_edit'] = True
        return kwargs

    def form_valid(self, form):
        with transaction.atomic():
            # Mettre à jour l'utilisateur Django
            user = self.object.user
            user.username = form.cleaned_data['username']
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']

            # Mettre à jour le mot de passe si fourni
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)

            user.save()

            # Sauvegarder le bénévole
            self.object = form.save()

            messages.success(self.request, 'Bénévole modifié avec succès.')
            return redirect(self.object.get_absolute_url())


@login_required
def volunteer_search_autocomplete(request):
    """Vue pour l'autocomplétion de recherche de bénévoles (pour HTMX)"""
    query = request.GET.get('q', '')
    volunteers = []

    if query and len(query) >= 2:
        volunteers = Volunteer.objects.select_related('user').filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__username__icontains=query)
        )[:10]

    if request.headers.get('HX-Request'):
        context = {'volunteers': volunteers, 'query': query}
        return render(request, 'volunteers/partials/search_results.html', context)

    # Fallback JSON pour autres usages
    results = [
        {
            'id': v.pk,
            'name': v.full_name,
            'email': v.user.email,
            'role': v.get_role_display(),
            'url': reverse('volunteers:detail', kwargs={'pk': v.pk})
        }
        for v in volunteers
    ]
    return JsonResponse({'results': results})
