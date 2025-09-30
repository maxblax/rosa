from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView,
    UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count
from datetime import datetime, timedelta, date
import json

from .models import (
    VolunteerCalendar, AvailabilitySlot, AvailabilityException, Appointment
)
from .forms import AppointmentForm, AvailabilitySlotForm


class CalendarPermissionMixin:
    """Mixin pour vérifier les permissions du calendrier"""

    def dispatch(self, request, *args, **kwargs):
        # Les superusers ont accès par défaut
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        # Vérifier que l'utilisateur a un profil volunteer et le droit au calendrier
        try:
            volunteer = request.user.volunteer_profile
            if volunteer is None:
                raise AttributeError("No volunteer profile")
        except AttributeError:
            messages.error(request, "Accès refusé : profil bénévole requis")
            return redirect('volunteers:list')
        if volunteer.role == 'VOLUNTEER_GOVERNANCE':
            messages.error(request, "Les bénévoles de gouvernance n'ont pas accès au calendrier")
            return redirect('volunteers:list')

        return super().dispatch(request, *args, **kwargs)

    def get_user_calendar(self):
        """Récupère ou crée le calendrier de l'utilisateur"""
        # Si l'utilisateur a un profil volunteer, utiliser son calendrier
        if hasattr(self.request.user, 'volunteer_profile') and self.request.user.volunteer_profile:
            volunteer = self.request.user.volunteer_profile
            calendar, created = VolunteerCalendar.objects.get_or_create(volunteer=volunteer)
            return calendar

        # Pour les superusers sans profil volunteer, créer un profil et calendrier
        if self.request.user.is_superuser:
            from volunteers.models import Volunteer
            volunteer, created = Volunteer.objects.get_or_create(
                user=self.request.user,
                defaults={
                    'role': 'ADMIN',
                    'phone': '',
                    'availability': 'Disponible à temps plein'
                }
            )
            calendar, created = VolunteerCalendar.objects.get_or_create(volunteer=volunteer)
            return calendar

        # Fallback: utiliser le premier calendrier disponible
        calendar = VolunteerCalendar.objects.first()
        if calendar:
            return calendar

        raise ValueError("Aucun calendrier disponible")


class CalendarView(LoginRequiredMixin, CalendarPermissionMixin, TemplateView):
    """Vue principale du calendrier - redirige vers la vue préférée"""

    def get(self, request, *args, **kwargs):
        calendar = self.get_user_calendar()
        view_type = request.GET.get('view', calendar.default_view)

        if view_type == 'day':
            return redirect('calendar:day')
        elif view_type == 'month':
            return redirect('calendar:month')
        else:
            return redirect('calendar:week')


class CalendarWeekView(LoginRequiredMixin, CalendarPermissionMixin, TemplateView):
    """Vue semaine du calendrier"""
    template_name = 'calendar/week.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar = self.get_user_calendar()

        # Récupérer la semaine depuis les paramètres GET ou utiliser semaine actuelle
        week_param = self.request.GET.get('week')
        if week_param:
            try:
                target_date = datetime.strptime(week_param, '%Y-%m-%d').date()
                week_start = target_date - timedelta(days=target_date.weekday())
            except ValueError:
                today = timezone.now().date()
                week_start = today - timedelta(days=today.weekday())
        else:
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())

        week_end = week_start + timedelta(days=6)

        # Navigation
        prev_week = week_start - timedelta(days=7)
        next_week = week_start + timedelta(days=7)

        # Récupérer les RDV de la semaine
        appointments = Appointment.objects.filter(
            volunteer_calendar=calendar,
            appointment_date__range=[week_start, week_end]
        ).select_related('beneficiary')

        # Créer la structure des jours de la semaine
        week_days = []
        for i in range(7):
            day_date = week_start + timedelta(days=i)
            day_appointments = [apt for apt in appointments if apt.appointment_date == day_date]

            # Récupérer les disponibilités pour ce jour
            weekday = day_date.weekday()
            day_slots = AvailabilitySlot.objects.filter(
                volunteer_calendar=calendar,
                is_active=True
            ).filter(
                Q(recurrence_type='WEEKLY', weekday=weekday) |
                Q(recurrence_type='NONE', specific_date=day_date)
            )

            week_days.append({
                'date': day_date,
                'weekday': day_date.weekday(),
                'appointments': day_appointments,
                'availability_slots': day_slots,
                'is_today': day_date == timezone.now().date()
            })

        # Générer toutes les heures de 6h à 23h (comme pour la vue jour)
        work_hours = []
        for hour in range(5, 24):
            # Déterminer si cette heure est dans la plage par défaut (8h-18h)
            is_default_hour = 8 <= hour <= 18

            work_hours.append({
                'hour': f"{hour:02d}:00",
                'hour_24': hour,
                'is_default': is_default_hour
            })

        # Récupérer les données pour les widgets de résumé
        week_appointments = appointments.order_by('appointment_date', 'start_time')
        week_availability_slots = AvailabilitySlot.objects.filter(
            volunteer_calendar=calendar,
            is_active=True
        ).order_by('weekday', 'start_time')

        context.update({
            'calendar': calendar,
            'week_start': week_start,
            'week_end': week_end,
            'prev_week': prev_week,
            'next_week': next_week,
            'week_days': week_days,
            'work_hours': work_hours,
            'appointments': week_appointments,
            'availability_slots': week_availability_slots,
            'current_view': 'week',
            'today': timezone.now().date(),
        })
        return context


class CalendarDayView(LoginRequiredMixin, CalendarPermissionMixin, TemplateView):
    """Vue jour du calendrier"""
    template_name = 'calendar/day.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar = self.get_user_calendar()

        # Récupérer la date depuis les paramètres GET ou utiliser aujourd'hui
        date_param = self.request.GET.get('date')
        if date_param:
            try:
                target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                target_date = timezone.now().date()
        else:
            target_date = timezone.now().date()

        # Récupérer les RDV du jour
        appointments = Appointment.objects.filter(
            volunteer_calendar=calendar,
            appointment_date=target_date
        ).select_related('beneficiary').order_by('start_time')

        # Récupérer les créneaux de disponibilité du jour
        weekday = target_date.weekday()
        availability_slots = AvailabilitySlot.objects.filter(
            volunteer_calendar=calendar,
            is_active=True
        ).filter(
            Q(recurrence_type='WEEKLY', weekday=weekday) |
            Q(recurrence_type='NONE', specific_date=target_date)
        )

        # Générer toutes les heures de 6h à 23h
        work_hours = []
        now = timezone.now()
        current_date = now.date()
        current_hour = now.hour

        for hour in range(5, 24):
            # Déterminer si cette heure est dans la plage par défaut (8h-18h)
            is_default_hour = 8 <= hour <= 18

            # Déterminer si cette heure est dans le passé
            is_past = False
            if target_date < current_date:
                is_past = True
            elif target_date == current_date:
                is_past = hour <= current_hour

            work_hours.append({
                'hour': f"{hour:02d}:00",
                'hour_24': hour,
                'appointments': [apt for apt in appointments if apt.start_time.hour == hour],
                'slots': [slot for slot in availability_slots if slot.start_time.hour <= hour < slot.end_time.hour],
                'is_default': is_default_hour,
                'is_past': is_past
            })

        # Navigation
        prev_date = target_date - timedelta(days=1)
        next_date = target_date + timedelta(days=1)

        context.update({
            'calendar': calendar,
            'target_date': target_date,
            'appointments': appointments,
            'availability_slots': availability_slots,
            'work_hours': work_hours,
            'prev_date': prev_date,
            'next_date': next_date,
            'current_view': 'day',
            'today': timezone.now().date(),
        })
        return context


class CalendarMonthView(LoginRequiredMixin, CalendarPermissionMixin, TemplateView):
    """Vue mois du calendrier - calendrier mensuel classique"""
    template_name = 'calendar/month.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar = self.get_user_calendar()

        # Mois actuel ou demandé
        month_param = self.request.GET.get('month')
        if month_param:
            try:
                target_date = datetime.strptime(month_param, '%Y-%m-%d').date()
                month_start = target_date.replace(day=1)
            except ValueError:
                month_start = timezone.now().date().replace(day=1)
        else:
            month_start = timezone.now().date().replace(day=1)

        # Calculer fin du mois
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month = month_start.replace(month=month_start.month + 1)
        month_end = next_month - timedelta(days=1)

        # Navigation
        prev_month = month_start - timedelta(days=1)
        prev_month = prev_month.replace(day=1)
        next_month_nav = next_month

        # Récupérer les RDV du mois
        appointments = Appointment.objects.filter(
            volunteer_calendar=calendar,
            appointment_date__range=[month_start, month_end]
        ).select_related('beneficiary')

        # Générer la grille du calendrier
        import calendar as cal
        month_calendar = cal.monthcalendar(month_start.year, month_start.month)

        # Créer une structure avec les rendez-vous par jour
        calendar_days = []
        for week in month_calendar:
            week_days = []
            for day in week:
                if day == 0:
                    week_days.append(None)
                else:
                    day_date = month_start.replace(day=day)
                    day_appointments = [a for a in appointments if a.appointment_date == day_date]
                    week_days.append({
                        'day': day,
                        'date': day_date,
                        'appointments': day_appointments,
                        'is_today': day_date == timezone.now().date()
                    })
            calendar_days.append(week_days)

        context.update({
            'calendar': calendar,
            'month_start': month_start,
            'month_end': month_end,
            'prev_month': prev_month,
            'next_month': next_month_nav,
            'appointments': appointments,
            'calendar_days': calendar_days,
            'current_view': 'month',
            'today': timezone.now().date(),
        })
        return context


class GlobalCalendarView(LoginRequiredMixin, TemplateView):
    """Vue globale équipe - planning type Google Calendar"""
    template_name = 'calendar/global.html'

    def dispatch(self, request, *args, **kwargs):
        # Les superusers ont accès par défaut
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        # Vérifier que l'utilisateur a les droits admin/salarié
        if not hasattr(request.user, 'volunteer_profile'):
            messages.error(request, "Accès refusé")
            return redirect('volunteers:list')

        volunteer = request.user.volunteer_profile
        if volunteer.role not in ['ADMIN', 'EMPLOYEE']:
            messages.error(request, "Accès refusé : droits administrateur requis")
            return redirect('calendar:main')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Récupérer la semaine depuis les paramètres GET
        week_param = self.request.GET.get('week')
        if week_param:
            try:
                target_date = datetime.strptime(week_param, '%Y-%m-%d').date()
                week_start = target_date - timedelta(days=target_date.weekday())
            except ValueError:
                today = timezone.now().date()
                week_start = today - timedelta(days=today.weekday())
        else:
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())

        week_end = week_start + timedelta(days=6)

        # Navigation
        prev_week = week_start - timedelta(days=7)
        next_week = week_start + timedelta(days=7)

        # Récupérer tous les calendriers actifs
        calendars = VolunteerCalendar.objects.filter(
            volunteer__role__in=['ADMIN', 'EMPLOYEE', 'VOLUNTEER_INTERVIEW']
        ).select_related('volunteer__user')

        # Récupérer tous les RDV et disponibilités de la semaine
        appointments = Appointment.objects.filter(
            appointment_date__range=[week_start, week_end]
        ).select_related('volunteer_calendar__volunteer__user', 'beneficiary')

        availability_slots = AvailabilitySlot.objects.filter(
            volunteer_calendar__in=calendars,
            is_active=True
        )

        # Organiser les données par jour de la semaine et par bénévole
        week_data = []
        for i in range(7):  # 7 jours de la semaine
            day_date = week_start + timedelta(days=i)

            # Récupérer les rendez-vous orphelins pour ce jour
            day_orphan_appointments = appointments.filter(
                volunteer_calendar__isnull=True,
                appointment_date=day_date
            ).order_by('start_time')

            day_data = {
                'date': day_date,
                'weekday': day_date.weekday(),
                'volunteers': [],
                'orphan_appointments': day_orphan_appointments
            }

            for calendar in calendars:
                # RDV du jour pour ce bénévole
                day_appointments = appointments.filter(
                    volunteer_calendar=calendar,
                    appointment_date=day_date
                ).order_by('start_time')

                # Disponibilités du jour pour ce bénévole
                day_slots = availability_slots.filter(
                    volunteer_calendar=calendar
                ).filter(
                    Q(recurrence_type='WEEKLY', weekday=day_date.weekday()) |
                    Q(recurrence_type='NONE', specific_date=day_date)
                ).order_by('start_time')

                volunteer_data = {
                    'calendar': calendar,
                    'appointments': day_appointments,
                    'availability_slots': day_slots
                }

                day_data['volunteers'].append(volunteer_data)

            week_data.append(day_data)


        # Organiser les données par bénévole et par heure (pour vue planning)
        hours_range = list(range(8, 21))  # 8h à 20h
        volunteers_data = []

        for calendar in calendars:
            volunteer_appointments = appointments.filter(volunteer_calendar=calendar)
            volunteer_slots = availability_slots.filter(volunteer_calendar=calendar)

            # Créer une liste ordonnée par heure pour les templates
            hours_list = []
            for hour in hours_range:
                hour_appointments = [apt for apt in volunteer_appointments if apt.start_time.hour == hour]
                hour_slots = [slot for slot in volunteer_slots
                             if slot.start_time.hour <= hour < slot.end_time.hour]

                hours_list.append({
                    'hour': hour,
                    'appointments': hour_appointments,
                    'slots': hour_slots
                })

            volunteers_data.append({
                'calendar': calendar,
                'volunteer': calendar.volunteer,
                'hours_list': hours_list
            })

        # Calculer les statistiques de la semaine
        total_hours = 0
        unique_beneficiaries = set()

        for appointment in appointments:
            # Calculer la durée de chaque rendez-vous
            start_datetime = datetime.combine(appointment.appointment_date, appointment.start_time)
            end_datetime = datetime.combine(appointment.appointment_date, appointment.end_time)
            duration = end_datetime - start_datetime
            total_hours += duration.total_seconds() / 3600  # Convertir en heures

            # Compter les bénéficiaires uniques
            unique_beneficiaries.add(appointment.beneficiary.id)

        # Récupérer tous les rendez-vous orphelins de la semaine
        orphan_appointments = appointments.filter(volunteer_calendar__isnull=True)

        context.update({
            'calendars': calendars,
            'week_start': week_start,
            'week_end': week_end,
            'prev_week': prev_week,
            'next_week': next_week,
            'appointments': appointments,
            'orphan_appointments': orphan_appointments,
            'volunteers_data': volunteers_data,
            'hours_range': hours_range,
            'week_data': week_data,
            'current_view': 'global',
            'total_hours': round(total_hours, 1),  # Arrondi à 1 décimale
            'unique_beneficiaries': len(unique_beneficiaries),
            'today': timezone.now().date(),
        })
        return context


class AvailabilityListView(LoginRequiredMixin, CalendarPermissionMixin, ListView):
    """Liste des créneaux de disponibilité"""
    model = AvailabilitySlot
    template_name = 'calendar/availability_list.html'
    context_object_name = 'slots'
    paginate_by = 20

    def get_queryset(self):
        calendar = self.get_user_calendar()
        return AvailabilitySlot.objects.filter(
            volunteer_calendar=calendar
        ).order_by('weekday', 'start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Récupérer tous les créneaux pour les statistiques (pas seulement la page courante)
        calendar = self.get_user_calendar()
        all_slots = AvailabilitySlot.objects.filter(volunteer_calendar=calendar)

        # Calculer le total d'heures par semaine
        total_hours = 0
        for slot in all_slots:
            if slot.is_active:
                # Calculer la durée du créneau
                start_datetime = datetime.combine(datetime.today(), slot.start_time)
                end_datetime = datetime.combine(datetime.today(), slot.end_time)
                duration = end_datetime - start_datetime
                hours = duration.total_seconds() / 3600

                # Si c'est hebdomadaire, on compte pour une semaine
                # Si c'est spécifique, on compte proportionnellement
                if slot.recurrence_type == 'WEEKLY':
                    total_hours += hours
                elif slot.recurrence_type == 'NONE':
                    # Pour les créneaux ponctuels, on peut les compter aussi
                    total_hours += hours

        # Compter les créneaux réservables et occupés
        bookable_slots = all_slots.filter(is_bookable=True, is_active=True).count()
        busy_slots = all_slots.filter(slot_type='BUSY', is_active=True).count()

        context.update({
            'total_hours': round(total_hours, 1),
            'bookable_slots': bookable_slots,
            'busy_slots': busy_slots,
        })

        return context


class AvailabilityCreateView(LoginRequiredMixin, CalendarPermissionMixin, CreateView):
    """Créer un nouveau créneau de disponibilité"""
    model = AvailabilitySlot
    template_name = 'calendar/availability_form.html'
    fields = [
        'slot_type', 'recurrence_type', 'weekday', 'specific_date',
        'start_time', 'end_time', 'valid_from', 'valid_until',
        'title', 'notes', 'is_bookable', 'max_appointments'
    ]
    success_url = reverse_lazy('calendar:availability_list')

    def form_valid(self, form):
        form.instance.volunteer_calendar = self.get_user_calendar()
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Créneau de disponibilité créé avec succès')
        return super().form_valid(form)


class AvailabilityDetailView(LoginRequiredMixin, CalendarPermissionMixin, DetailView):
    """Détail d'un créneau de disponibilité"""
    model = AvailabilitySlot
    template_name = 'calendar/availability_detail.html'
    context_object_name = 'slot'

    def get_queryset(self):
        calendar = self.get_user_calendar()
        return AvailabilitySlot.objects.filter(volunteer_calendar=calendar)


class AvailabilityEditView(LoginRequiredMixin, CalendarPermissionMixin, UpdateView):
    """Modifier un créneau de disponibilité"""
    model = AvailabilitySlot
    template_name = 'calendar/availability_form.html'
    fields = [
        'slot_type', 'recurrence_type', 'weekday', 'specific_date',
        'start_time', 'end_time', 'valid_from', 'valid_until',
        'title', 'notes', 'is_bookable', 'max_appointments', 'is_active'
    ]
    success_url = reverse_lazy('calendar:availability_list')

    def get_queryset(self):
        calendar = self.get_user_calendar()
        return AvailabilitySlot.objects.filter(volunteer_calendar=calendar)

    def form_valid(self, form):
        messages.success(self.request, 'Créneau de disponibilité modifié avec succès')
        return super().form_valid(form)


class AvailabilityDeleteView(LoginRequiredMixin, CalendarPermissionMixin, DeleteView):
    """Supprimer un créneau de disponibilité"""
    model = AvailabilitySlot
    template_name = 'calendar/availability_confirm_delete.html'
    success_url = reverse_lazy('calendar:availability_list')

    def get_queryset(self):
        calendar = self.get_user_calendar()
        return AvailabilitySlot.objects.filter(volunteer_calendar=calendar)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Créneau de disponibilité supprimé avec succès')
        return super().delete(request, *args, **kwargs)


class AppointmentListView(LoginRequiredMixin, CalendarPermissionMixin, ListView):
    """Liste des rendez-vous"""
    model = Appointment
    template_name = 'calendar/appointment_list.html'
    context_object_name = 'appointments'
    paginate_by = 20

    def get_queryset(self):
        calendar = self.get_user_calendar()
        return Appointment.objects.filter(
            volunteer_calendar=calendar
        ).select_related('beneficiary')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from django.utils import timezone

        # Récupérer tous les rendez-vous pour calculer les statistiques
        calendar = self.get_user_calendar()
        all_appointments = Appointment.objects.filter(volunteer_calendar=calendar).select_related('beneficiary')

        # Date d'aujourd'hui
        today = timezone.now().date()

        # Séparer les rendez-vous futurs et passés
        future_appointments = all_appointments.filter(
            appointment_date__gte=today
        ).order_by('appointment_date', 'start_time')

        past_appointments = all_appointments.filter(
            appointment_date__lt=today
        ).order_by('-appointment_date', '-start_time')  # Plus récents en premier

        # Combiner dans l'ordre : futurs puis passés
        appointments_list = list(future_appointments) + list(past_appointments)

        # Remplacer la liste des appointments dans le context
        context['appointments'] = appointments_list
        context['future_appointments'] = future_appointments
        context['past_appointments'] = past_appointments
        context['today'] = today

        # Calculer les compteurs par statut
        context['scheduled_count'] = all_appointments.filter(status='SCHEDULED').count()
        context['confirmed_count'] = all_appointments.filter(status='CONFIRMED').count()
        context['completed_count'] = all_appointments.filter(status='COMPLETED').count()
        context['cancelled_count'] = all_appointments.filter(status='CANCELLED').count()
        context['in_progress_count'] = all_appointments.filter(status='IN_PROGRESS').count()
        context['no_show_count'] = all_appointments.filter(status='NO_SHOW').count()

        return context


class AppointmentCreateView(LoginRequiredMixin, CalendarPermissionMixin, CreateView):
    """Créer un nouveau rendez-vous"""
    model = Appointment
    form_class = AppointmentForm
    template_name = 'calendar/appointment_form.html'
    success_url = reverse_lazy('calendar:appointment_list')

    def calculate_real_availability(self, availability_slots, appointments):
        """
        Calcule les disponibilités réelles en soustrayant les rendez-vous existants.
        Retourne des créneaux libres.
        """
        real_slots = []

        for slot in availability_slots:
            current_slots = [{
                'start_time': slot.start_time,
                'end_time': slot.end_time,
                'slot': slot
            }]

            # Pour chaque rendez-vous, découper les créneaux disponibles
            for appointment in appointments:
                new_slots = []
                for current_slot in current_slots:
                    # Si le RDV ne chevauche pas avec ce créneau, le garder tel quel
                    if (appointment.end_time <= current_slot['start_time'] or
                        appointment.start_time >= current_slot['end_time']):
                        new_slots.append(current_slot)
                    else:
                        # Le RDV chevauche, découper le créneau
                        # Partie avant le RDV
                        if appointment.start_time > current_slot['start_time']:
                            new_slots.append({
                                'start_time': current_slot['start_time'],
                                'end_time': appointment.start_time,
                                'slot': current_slot['slot']
                            })

                        # Partie après le RDV
                        if appointment.end_time < current_slot['end_time']:
                            new_slots.append({
                                'start_time': appointment.end_time,
                                'end_time': current_slot['end_time'],
                                'slot': current_slot['slot']
                            })

                current_slots = new_slots

            # Ajouter les créneaux libres restants (au moins 30 minutes)
            for free_slot in current_slots:
                duration = datetime.combine(date.today(), free_slot['end_time']) - datetime.combine(date.today(), free_slot['start_time'])
                if duration.total_seconds() >= 1800:  # Au moins 30 minutes
                    real_slots.append({
                        'id': free_slot['slot'].id,
                        'start_time': free_slot['start_time'],
                        'end_time': free_slot['end_time'],
                        'title': free_slot['slot'].title,
                        'original_slot': free_slot['slot']
                    })

        return real_slots

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # Pré-remplir avec les paramètres GET
        initial['appointment_date'] = self.request.GET.get('date')  # Correction: utiliser 'appointment_date' au lieu de 'date'
        initial['time'] = self.request.GET.get('time')
        initial['start_time'] = self.request.GET.get('start_time')
        initial['end_time'] = self.request.GET.get('end_time')

        # Pré-remplir le bénéficiaire si spécifié
        beneficiary_id = self.request.GET.get('beneficiary')
        if beneficiary_id:
            initial['beneficiary'] = beneficiary_id

        # Pré-remplir le calendrier bénévole - utiliser le calendrier de l'utilisateur actuel par défaut
        volunteer_calendar_id = self.request.GET.get('volunteer_calendar')
        if volunteer_calendar_id:
            initial['volunteer_calendar'] = volunteer_calendar_id
        else:
            # Utiliser automatiquement le calendrier de l'utilisateur actuel
            try:
                user_calendar = self.get_user_calendar()
                initial['volunteer_calendar'] = user_calendar.id
            except:
                pass

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Récupérer la semaine depuis les paramètres GET ou utiliser semaine actuelle
        week_param = self.request.GET.get('week')
        if week_param:
            try:
                target_date = datetime.strptime(week_param, '%Y-%m-%d').date()
                week_start = target_date - timedelta(days=target_date.weekday())
            except ValueError:
                today = timezone.now().date()
                week_start = today - timedelta(days=today.weekday())
        else:
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())

        week_end = week_start + timedelta(days=6)

        # Navigation
        prev_week = week_start - timedelta(days=7)
        next_week = week_start + timedelta(days=7)

        # Récupérer tous les calendriers actifs
        calendars = VolunteerCalendar.objects.filter(
            volunteer__role__in=['ADMIN', 'EMPLOYEE', 'VOLUNTEER_INTERVIEW']
        ).select_related('volunteer__user')

        # Récupérer tous les RDV et disponibilités de la semaine
        appointments = Appointment.objects.filter(
            appointment_date__range=[week_start, week_end]
        ).select_related('volunteer_calendar__volunteer__user', 'beneficiary')

        availability_slots = AvailabilitySlot.objects.filter(
            volunteer_calendar__in=calendars,
            is_active=True
        )

        # Organiser les données par jour de la semaine et par bénévole
        week_data = []
        for i in range(7):  # 7 jours de la semaine
            day_date = week_start + timedelta(days=i)
            day_data = {
                'date': day_date,
                'weekday': day_date.weekday(),
                'volunteers': []
            }

            for calendar in calendars:
                # RDV du jour pour ce bénévole
                day_appointments = appointments.filter(
                    volunteer_calendar=calendar,
                    appointment_date=day_date
                ).order_by('start_time')

                # Disponibilités du jour pour ce bénévole
                day_slots = availability_slots.filter(
                    volunteer_calendar=calendar
                ).filter(
                    Q(recurrence_type='WEEKLY', weekday=day_date.weekday()) |
                    Q(recurrence_type='NONE', specific_date=day_date)
                ).order_by('start_time')

                # Calculer les disponibilités réelles (disponibilités - rendez-vous)
                real_availability_slots = self.calculate_real_availability(day_slots, day_appointments)

                # Filtrer les créneaux passés : ne pas afficher les créneaux qui sont dans le passé
                today = timezone.now().date()
                current_time = timezone.now().time()
                filtered_slots = []

                for slot in real_availability_slots:
                    # Garder les créneaux des jours futurs
                    if day_date > today:
                        filtered_slots.append(slot)
                    # Pour aujourd'hui, garder seulement les créneaux dont l'heure de fin n'est pas encore passée
                    elif day_date == today and slot['end_time'] > current_time:
                        filtered_slots.append(slot)
                    # Ignorer complètement les créneaux passés

                real_availability_slots = filtered_slots

                volunteer_data = {
                    'calendar': calendar,
                    'appointments': [],  # Masquer les RDV dans la vue création
                    'availability_slots': real_availability_slots  # Seulement les créneaux libres
                }

                day_data['volunteers'].append(volunteer_data)

            week_data.append(day_data)

        # Ajouter au contexte
        context.update({
            'calendars': calendars,
            'week_start': week_start,
            'week_end': week_end,
            'prev_week': prev_week,
            'next_week': next_week,
            'week_data': week_data,
            'today': timezone.now().date(),
        })

        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Rendez-vous créé avec succès')
        return super().form_valid(form)


class AppointmentDetailView(LoginRequiredMixin, CalendarPermissionMixin, DetailView):
    """Détail d'un rendez-vous"""
    model = Appointment
    template_name = 'calendar/appointment_detail.html'
    context_object_name = 'appointment'

    def get_queryset(self):
        # Filtrer les rendez-vous selon les permissions
        user = self.request.user
        if user.is_superuser:
            return Appointment.objects.all()

        try:
            volunteer = user.volunteer_profile
            if volunteer.role in ['ADMIN', 'EMPLOYEE']:
                # Admins et employés peuvent voir tous les rendez-vous
                return Appointment.objects.all()
            elif volunteer.role == 'VOLUNTEER_INTERVIEW':
                # Bénévoles d'entretien peuvent voir tous les rendez-vous
                return Appointment.objects.all()
            else:
                # Autres rôles : seulement leurs rendez-vous
                calendar = VolunteerCalendar.objects.filter(volunteer=volunteer).first()
                if calendar:
                    return Appointment.objects.filter(volunteer_calendar=calendar)
        except AttributeError:
            pass

        return Appointment.objects.none()


class AppointmentEditView(LoginRequiredMixin, CalendarPermissionMixin, UpdateView):
    """Modifier un rendez-vous"""
    model = Appointment
    form_class = AppointmentForm
    template_name = 'calendar/appointment_form.html'
    success_url = reverse_lazy('calendar:appointment_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        # Filtrer les rendez-vous selon les permissions
        user = self.request.user
        if user.is_superuser:
            return Appointment.objects.all()

        try:
            volunteer = user.volunteer_profile
            if volunteer.role in ['ADMIN', 'EMPLOYEE']:
                # Admins et employés peuvent modifier tous les rendez-vous
                return Appointment.objects.all()
            elif volunteer.role == 'VOLUNTEER_INTERVIEW':
                # Bénévoles d'entretien peuvent voir tous les rendez-vous mais modifier seulement les leurs
                calendar = VolunteerCalendar.objects.filter(volunteer=volunteer).first()
                if calendar:
                    return Appointment.objects.filter(volunteer_calendar=calendar)
            else:
                # Autres rôles : seulement leurs rendez-vous
                calendar = VolunteerCalendar.objects.filter(volunteer=volunteer).first()
                if calendar:
                    return Appointment.objects.filter(volunteer_calendar=calendar)
        except AttributeError:
            pass

        return Appointment.objects.none()

    def form_valid(self, form):
        messages.success(self.request, 'Rendez-vous modifié avec succès')
        return super().form_valid(form)


class AppointmentDeleteView(LoginRequiredMixin, CalendarPermissionMixin, DeleteView):
    """Supprimer un rendez-vous"""
    model = Appointment
    template_name = 'calendar/appointment_confirm_delete.html'
    success_url = reverse_lazy('calendar:appointment_list')

    def get_queryset(self):
        calendar = self.get_user_calendar()
        return Appointment.objects.filter(volunteer_calendar=calendar)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Rendez-vous supprimé avec succès')
        return super().delete(request, *args, **kwargs)


class CalendarSettingsView(LoginRequiredMixin, CalendarPermissionMixin, UpdateView):
    """Paramètres du calendrier"""
    model = VolunteerCalendar
    template_name = 'calendar/settings.html'
    fields = [
        'default_view', 'work_start_time', 'work_end_time',
        'show_weekends', 'email_reminders', 'reminder_hours_before'
    ]
    success_url = reverse_lazy('calendar:main')

    def get_object(self):
        return self.get_user_calendar()

    def form_valid(self, form):
        messages.success(self.request, 'Paramètres du calendrier mis à jour')
        return super().form_valid(form)


# API Views pour HTMX
@login_required
def api_availability_slots(request):
    """API pour récupérer les créneaux de disponibilité"""
    if not hasattr(request.user, 'volunteer_profile'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    calendar = VolunteerCalendar.objects.get(volunteer=request.user.volunteer_profile)

    slots = AvailabilitySlot.objects.filter(
        volunteer_calendar=calendar,
        is_active=True
    ).values(
        'id', 'weekday', 'start_time', 'end_time', 'slot_type',
        'recurrence_type', 'title'
    )

    return JsonResponse(list(slots), safe=False)


@login_required
def api_appointments(request):
    """API pour récupérer les rendez-vous"""
    if not hasattr(request.user, 'volunteer_profile'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    calendar = VolunteerCalendar.objects.get(volunteer=request.user.volunteer_profile)

    # Filtres de date
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    appointments = Appointment.objects.filter(volunteer_calendar=calendar)

    if start_date and end_date:
        appointments = appointments.filter(
            appointment_date__range=[start_date, end_date]
        )

    appointments = appointments.select_related('beneficiary').values(
        'id', 'appointment_date', 'start_time', 'end_time',
        'title', 'appointment_type', 'status', 'location',
        'beneficiary__first_name', 'beneficiary__last_name'
    )

    return JsonResponse(list(appointments), safe=False)


@login_required
def api_calendar_data(request):
    """API complète pour les données du calendrier"""
    if not hasattr(request.user, 'volunteer_profile'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    calendar = VolunteerCalendar.objects.get(volunteer=request.user.volunteer_profile)

    # Période demandée
    start_date = request.GET.get('start', timezone.now().date().isoformat())
    end_date = request.GET.get('end', (timezone.now().date() + timedelta(days=7)).isoformat())

    # Récupérer les données
    slots = AvailabilitySlot.objects.filter(
        volunteer_calendar=calendar,
        is_active=True
    )

    appointments = Appointment.objects.filter(
        volunteer_calendar=calendar,
        appointment_date__range=[start_date, end_date]
    ).select_related('beneficiary')

    data = {
        'calendar_settings': {
            'default_view': calendar.default_view,
            'work_start_time': calendar.work_start_time.strftime('%H:%M'),
            'work_end_time': calendar.work_end_time.strftime('%H:%M'),
            'show_weekends': calendar.show_weekends,
        },
        'availability_slots': [],
        'appointments': []
    }

    # Formater les créneaux
    for slot in slots:
        occurrences = slot.get_occurrences_in_range(
            datetime.fromisoformat(start_date).date(),
            datetime.fromisoformat(end_date).date()
        )
        data['availability_slots'].extend(occurrences)

    # Formater les RDV
    for appointment in appointments:
        data['appointments'].append({
            'id': appointment.id,
            'date': appointment.appointment_date.isoformat(),
            'start_time': appointment.start_time.strftime('%H:%M'),
            'end_time': appointment.end_time.strftime('%H:%M'),
            'title': appointment.title,
            'beneficiary': f"{appointment.beneficiary.first_name} {appointment.beneficiary.last_name}",
            'type': appointment.appointment_type,
            'status': appointment.status,
            'location': appointment.location,
        })

    return JsonResponse(data)


@login_required
def volunteer_availability_api(request):
    """API HTMX pour afficher les disponibilités d'un bénévole"""
    if request.headers.get('HX-Request') != 'true':
        return JsonResponse({'error': 'HTMX required'}, status=400)

    volunteer_calendar_id = request.GET.get('volunteer_calendar')
    appointment_date = request.GET.get('appointment_date')
    start_time = request.GET.get('start_time')

    if not all([volunteer_calendar_id, appointment_date]):
        return render(request, 'calendar/partials/availability_panel.html', {
            'message': 'Sélectionnez un bénévole et une date pour voir les disponibilités.'
        })

    try:
        volunteer_calendar = VolunteerCalendar.objects.get(id=volunteer_calendar_id)
        date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
    except (VolunteerCalendar.DoesNotExist, ValueError):
        return render(request, 'calendar/partials/availability_panel.html', {
            'error': 'Bénévole ou date invalide.'
        })

    # Récupérer les disponibilités pour cette date
    weekday = date_obj.weekday()
    availability_slots = AvailabilitySlot.objects.filter(
        volunteer_calendar=volunteer_calendar,
        is_active=True
    ).filter(
        Q(recurrence_type='WEEKLY', weekday=weekday) |
        Q(recurrence_type='ONCE', specific_date=date_obj)
    ).order_by('start_time')

    # Récupérer les RDV existants pour cette date
    existing_appointments = Appointment.objects.filter(
        volunteer_calendar=volunteer_calendar,
        appointment_date=date_obj
    ).order_by('start_time')

    # Vérifier les conflits si une heure de début est spécifiée
    conflict_detected = False
    if start_time:
        try:
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            # Vérifier s'il y a un conflit (approximatif, assume 1h de durée)
            end_time_obj = (datetime.combine(date_obj, start_time_obj) + timedelta(hours=1)).time()

            conflict_detected = existing_appointments.filter(
                start_time__lt=end_time_obj,
                end_time__gt=start_time_obj
            ).exists()
        except ValueError:
            pass

    context = {
        'volunteer_calendar': volunteer_calendar,
        'appointment_date': date_obj,
        'availability_slots': availability_slots,
        'existing_appointments': existing_appointments,
        'conflict_detected': conflict_detected,
        'selected_time': start_time,
    }

    return render(request, 'calendar/partials/availability_panel.html', context)


@login_required
@require_http_methods(["GET"])
def available_volunteers_api(request):
    """
    API HTMX pour récupérer les bénévoles disponibles selon date et heure.
    Retourne les options HTML pour le champ volunteer_calendar.
    """
    from django.http import HttpResponse
    from datetime import datetime

    # Récupérer les paramètres
    appointment_date = request.GET.get('appointment_date')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')

    # Si on n'a pas toutes les infos, retourner le placeholder
    if not all([appointment_date, start_time, end_time]):
        html = '<option value="">--- Choisir la date et l\'heure d\'abord ---</option>'
        return HttpResponse(html)

    try:
        # Parse des dates/heures
        apt_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        start_dt = datetime.strptime(start_time, '%H:%M').time()
        end_dt = datetime.strptime(end_time, '%H:%M').time()

        # Vérifier logique temporelle
        if end_dt <= start_dt:
            html = '<option value="">Heure de fin doit être après heure de début</option>'
            return HttpResponse(html)

    except ValueError:
        html = '<option value="">Format date/heure invalide</option>'
        return HttpResponse(html)

    # Récupérer tous les calendriers actifs (sauf gouvernance)
    from django.db.models import Q

    all_calendars = VolunteerCalendar.objects.filter(
        volunteer__role__in=['ADMIN', 'EMPLOYEE', 'VOLUNTEER_INTERVIEW']
    ).select_related('volunteer__user').order_by('volunteer__user__last_name', 'volunteer__user__first_name')

    weekday = apt_date.weekday()
    available_calendars = []

    for calendar in all_calendars:
        # Vérifier disponibilités pour ce créneau
        availability_slots = AvailabilitySlot.objects.filter(
            volunteer_calendar=calendar,
            is_active=True
        ).filter(
            Q(recurrence_type='WEEKLY', weekday=weekday) |
            Q(recurrence_type='NONE', specific_date=apt_date)
        )

        # Vérifier si le bénévole est disponible pendant ce créneau
        is_available = False
        for slot in availability_slots:
            if (slot.start_time <= start_dt and end_dt <= slot.end_time):
                is_available = True
                break

        if is_available:
            # Vérifier qu'il n'y a pas de conflit avec RDV existants
            conflicting_appointments = Appointment.objects.filter(
                volunteer_calendar=calendar,
                appointment_date=apt_date,
                start_time__lt=end_dt,
                end_time__gt=start_dt
            )

            if not conflicting_appointments.exists():
                available_calendars.append(calendar)

    # Générer les options HTML
    html_options = ['<option value="">--- Aucun bénévole assigné (optionnel) ---</option>']

    if available_calendars:
        html_options.append('<optgroup label="Bénévoles disponibles">')
        for calendar in available_calendars:
            volunteer_name = calendar.volunteer.user.get_full_name()
            html_options.append(f'<option value="{calendar.pk}">{volunteer_name} ✓</option>')
        html_options.append('</optgroup>')

    # Ajouter tous les autres bénévoles comme "occupés" ou "indisponibles"
    unavailable_calendars = [c for c in all_calendars if c not in available_calendars]
    if unavailable_calendars:
        html_options.append('<optgroup label="Bénévoles indisponibles">')
        for calendar in unavailable_calendars:
            volunteer_name = calendar.volunteer.user.get_full_name()
            html_options.append(f'<option value="{calendar.pk}" class="text-gray-400">{volunteer_name} ⚠️</option>')
        html_options.append('</optgroup>')

    return HttpResponse('\n'.join(html_options))


# Vues HTMX pour les panels de disponibilité

@login_required
def availability_edit_panel(request, pk):
    """Panel HTMX pour éditer une disponibilité existante"""
    try:
        calendar = get_object_or_404(VolunteerCalendar, volunteer__user=request.user)
        slot = get_object_or_404(AvailabilitySlot, pk=pk, volunteer_calendar=calendar)
    except:
        return HttpResponse('<div class="p-4 text-red-600">Erreur: créneau non trouvé</div>')

    if request.method == 'POST':
        if 'delete' in request.POST:
            # Supprimer le créneau
            slot.delete()
            return HttpResponse('<script>setTimeout(() => { window.location.reload(); }, 300);</script>')
        else:
            # Mettre à jour le créneau
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')

            if start_time and end_time:
                try:
                    from datetime import datetime
                    new_start = datetime.strptime(start_time, '%H:%M').time()
                    new_end = datetime.strptime(end_time, '%H:%M').time()

                    # Validation: l'heure de fin doit être après l'heure de début
                    if new_end <= new_start:
                        return HttpResponse('<div class="p-4 text-red-600">Erreur: L\'heure de fin doit être après l\'heure de début</div>')

                    slot.start_time = new_start
                    slot.end_time = new_end
                    slot.save()
                    return HttpResponse('<script>setTimeout(() => { window.location.reload(); }, 200);</script>')
                except ValueError:
                    return HttpResponse('<div class="p-4 text-red-600">Erreur: Format d\'heure invalide</div>')

    # Rendu du panel d'édition
    return render(request, 'calendar/partials/availability_edit_panel.html', {
        'slot': slot,
    })


@login_required
def availability_new_panel(request):
    """Panel HTMX pour créer une nouvelle disponibilité"""
    try:
        calendar = get_object_or_404(VolunteerCalendar, volunteer__user=request.user)
    except:
        return HttpResponse('<div class="p-4 text-red-600">Erreur: calendrier non trouvé</div>')

    # Paramètres de la requête
    date = request.GET.get('date')
    hour = request.GET.get('hour')
    start_hour = request.GET.get('start_hour')
    end_hour = request.GET.get('end_hour')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_availability':
            # Créer une nouvelle disponibilité
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            slot_date = request.POST.get('date')

            if start_time and end_time and slot_date:
                try:
                    from datetime import datetime
                    from django.utils import timezone

                    # Vérifier que ce n'est pas dans le passé
                    target_date = datetime.strptime(slot_date, '%Y-%m-%d').date()
                    target_start_time = datetime.strptime(start_time, '%H:%M').time()
                    now = timezone.now()
                    current_date = now.date()

                    # Bloquer si la date est passée
                    if target_date < current_date:
                        return HttpResponse('<div class="p-4 text-red-600">Erreur: Impossible de créer une disponibilité dans le passé</div>')

                    # Si c'est aujourd'hui, vérifier l'heure
                    if target_date == current_date:
                        target_datetime = datetime.combine(target_date, target_start_time)
                        current_datetime = now.replace(tzinfo=None)
                        if target_datetime <= current_datetime:
                            return HttpResponse('<div class="p-4 text-red-600">Erreur: Impossible de créer une disponibilité à une heure passée</div>')

                    # Créer un titre par défaut
                    title = f"Disponibilité {start_time}-{end_time}"

                    slot = AvailabilitySlot.objects.create(
                        volunteer_calendar=calendar,
                        title=title,
                        slot_type='AVAILABILITY',
                        recurrence_type='NONE',
                        specific_date=target_date,
                        start_time=target_start_time,
                        end_time=datetime.strptime(end_time, '%H:%M').time(),
                        is_bookable=True,
                        is_active=True,
                        created_by=request.user
                    )
                    return HttpResponse('<script>window.location.reload();</script>')
                except Exception as e:
                    return HttpResponse(f'<div class="p-4 text-red-600">Erreur lors de la création: {str(e)}</div>')

        elif action == 'create_appointment':
            # Redirection vers la création de RDV avec paramètres pré-remplis
            start_time = request.POST.get('start_time')
            slot_date = request.POST.get('date')

            # Vérifier que ce n'est pas dans le passé avant la redirection
            if slot_date:
                try:
                    from datetime import datetime
                    from django.utils import timezone

                    target_date = datetime.strptime(slot_date, '%Y-%m-%d').date()
                    now = timezone.now()
                    current_date = now.date()

                    # Bloquer si la date est passée
                    if target_date < current_date:
                        return HttpResponse('<div class="p-4 text-red-600">Erreur: Impossible de créer un rendez-vous dans le passé</div>')

                    # Si c'est aujourd'hui et qu'on a l'heure, vérifier l'heure
                    if target_date == current_date and start_time:
                        try:
                            target_start_time = datetime.strptime(start_time, '%H:%M').time()
                            target_datetime = datetime.combine(target_date, target_start_time)
                            current_datetime = now.replace(tzinfo=None)
                            if target_datetime <= current_datetime:
                                return HttpResponse('<div class="p-4 text-red-600">Erreur: Impossible de créer un rendez-vous à une heure passée</div>')
                        except:
                            pass

                except:
                    pass

            url = f"/calendrier/appointments/create/?date={slot_date}"
            if start_time:
                url += f"&time={start_time}"
            return HttpResponse(f'<script>window.location.href = "{url}";</script>')

    # Vérifier si c'est dans le passé
    is_past_date = False
    if date:
        try:
            from datetime import datetime
            from django.utils import timezone

            target_date = datetime.strptime(date, '%Y-%m-%d').date()
            now = timezone.now()
            current_date = now.date()

            # Si c'est une date passée, ou si c'est aujourd'hui mais l'heure est passée
            is_past_date = target_date < current_date

            # Si c'est aujourd'hui, vérifier l'heure aussi
            if target_date == current_date and hour:
                try:
                    target_hour = int(hour) if isinstance(hour, int) else int(hour.split(':')[0])
                    current_hour = now.hour
                    is_past_date = target_hour <= current_hour
                except:
                    pass

        except:
            pass

    # Valeurs par défaut
    try:
        if hour:
            default_start = f"{hour:02d}:00" if isinstance(hour, int) else f"{hour}:00"
            next_hour = int(hour) + 1 if isinstance(hour, int) else int(hour.split(':')[0]) + 1
            default_end = f"{next_hour:02d}:00"
        elif start_hour:
            default_start = f"{start_hour}:00"
            default_end = f"{end_hour or int(start_hour) + 1}:00"
        else:
            default_start = "09:00"
            default_end = "10:00"
    except:
        default_start = "09:00"
        default_end = "10:00"

    return render(request, 'calendar/partials/availability_new_panel.html', {
        'calendar': calendar,
        'date': date,
        'default_start': default_start,
        'default_end': default_end,
        'is_past': is_past_date,
    })