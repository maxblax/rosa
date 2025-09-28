from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, date
from .models import Volunteer, TimeTracking
from .forms import VolunteerForm, TimeTrackingForm


class VolunteerListView(ListView):
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


class VolunteerCreateView(CreateView):
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


class VolunteerDetailView(DetailView):
    """Vue détail d'un bénévole avec historique des heures"""
    model = Volunteer
    template_name = 'volunteers/detail.html'
    context_object_name = 'volunteer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['time_trackings'] = self.object.time_trackings.all()[:12]  # Derniers 12 mois
        context['latest_time_tracking'] = self.object.latest_time_tracking

        # Calculer les statistiques
        current_year = date.today().year
        year_trackings = self.object.time_trackings.filter(month__year=current_year)
        context['total_hours_this_year'] = sum(t.hours_worked for t in year_trackings)
        context['months_tracked_this_year'] = year_trackings.count()

        return context


class VolunteerUpdateView(UpdateView):
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


class TimeTrackingCreateView(CreateView):
    """Vue pour créer un suivi d'heures pour un bénévole"""
    model = TimeTracking
    form_class = TimeTrackingForm
    template_name = 'volunteers/time_tracking_create.html'

    def dispatch(self, request, *args, **kwargs):
        self.volunteer = get_object_or_404(Volunteer, pk=kwargs['volunteer_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['volunteer'] = self.volunteer
        return context

    def form_valid(self, form):
        # Le formulaire a déjà converti le mois en date
        first_day_of_month = form.cleaned_data['month']

        self.object = form.save(commit=False)
        self.object.volunteer = self.volunteer
        self.object.month = first_day_of_month

        # Vérifier qu'il n'y a pas déjà un suivi pour ce mois
        existing = TimeTracking.objects.filter(
            volunteer=self.volunteer,
            month=first_day_of_month
        ).exists()

        if existing:
            messages.error(
                self.request,
                f'Un suivi d\'heures existe déjà pour {first_day_of_month.strftime("%B %Y")}.'
            )
            return self.form_invalid(form)

        self.object.save()

        messages.success(
            self.request,
            f'Suivi d\'heures pour {first_day_of_month.strftime("%B %Y")} créé avec succès.'
        )

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('volunteers:detail', kwargs={'pk': self.volunteer.pk})


class TimeTrackingUpdateView(UpdateView):
    """Vue pour modifier un suivi d'heures"""
    model = TimeTracking
    form_class = TimeTrackingForm
    template_name = 'volunteers/time_tracking_edit.html'
    context_object_name = 'time_tracking'

    def get_object(self):
        return get_object_or_404(
            TimeTracking,
            pk=self.kwargs['pk'],
            volunteer__pk=self.kwargs['volunteer_pk']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['volunteer'] = self.object.volunteer
        return context

    def form_valid(self, form):
        # Le formulaire a déjà converti le mois en date
        first_day_of_month = form.cleaned_data['month']

        self.object = form.save(commit=False)
        self.object.month = first_day_of_month

        # Vérifier qu'il n'y a pas déjà un autre suivi pour ce mois
        existing = TimeTracking.objects.filter(
            volunteer=self.object.volunteer,
            month=first_day_of_month
        ).exclude(pk=self.object.pk).exists()

        if existing:
            messages.error(
                self.request,
                f'Un autre suivi d\'heures existe déjà pour {first_day_of_month.strftime("%B %Y")}.'
            )
            return self.form_invalid(form)

        self.object.save()

        messages.success(self.request, 'Suivi d\'heures modifié avec succès.')
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('volunteers:detail', kwargs={'pk': self.object.volunteer.pk})


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
