from django import forms
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Appointment, AvailabilitySlot, VolunteerCalendar
from volunteers.models import Volunteer
from beneficiaries.models import Beneficiary


class AppointmentForm(forms.ModelForm):
    beneficiary = forms.ModelChoiceField(
        queryset=Beneficiary.objects.all(),
        label="Bénéficiaire",
        help_text="Sélectionnez d'abord le bénéficiaire pour ce rendez-vous",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )

    volunteer_calendar = forms.ModelChoiceField(
        queryset=VolunteerCalendar.objects.none(),
        label="Bénévole (recommandé)",
        help_text="Les bénévoles disponibles s'affichent selon la date et l'heure choisies",
        required=False,
        empty_label="--- Choisir la date et l'heure d'abord ---",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'hx-get': '/calendrier/api/available-volunteers/',
            'hx-target': '#volunteer-availability-info',
            'hx-trigger': 'change',
            'hx-include': '#id_appointment_date, #id_start_time, #id_end_time'
        })
    )

    appointment_date = forms.DateField(
        label="Date du rendez-vous",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'hx-get': '/calendrier/api/available-volunteers/',
            'hx-target': '#id_volunteer_calendar',
            'hx-trigger': 'change',
            'hx-include': '#id_start_time, #id_end_time'
        })
    )

    start_time = forms.TimeField(
        label="Heure de début",
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'hx-get': '/calendrier/api/available-volunteers/',
            'hx-target': '#id_volunteer_calendar',
            'hx-trigger': 'change',
            'hx-include': '#id_appointment_date, #id_end_time'
        })
    )

    end_time = forms.TimeField(
        label="Heure de fin",
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'hx-get': '/calendrier/api/available-volunteers/',
            'hx-target': '#id_volunteer_calendar',
            'hx-trigger': 'change',
            'hx-include': '#id_appointment_date, #id_start_time'
        })
    )

    appointment_type = forms.ChoiceField(
        choices=Appointment.APPOINTMENT_TYPES,
        label="Type de rendez-vous",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )

    title = forms.CharField(
        label="Titre",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Titre du rendez-vous'
        })
    )

    description = forms.CharField(
        label="Description",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'rows': 4,
            'placeholder': 'Description détaillée du rendez-vous'
        })
    )

    location = forms.CharField(
        label="Lieu",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Lieu du rendez-vous'
        })
    )

    preparation_notes = forms.CharField(
        label="Notes de préparation",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'rows': 3,
            'placeholder': 'Notes pour préparer le rendez-vous'
        })
    )

    class Meta:
        model = Appointment
        fields = [
            'beneficiary', 'appointment_date', 'start_time', 'end_time',
            'volunteer_calendar', 'appointment_type', 'title',
            'description', 'location', 'preparation_notes'
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            # Filtrer les calendriers selon les permissions
            if user.is_superuser:
                # Les superusers voient tous les calendriers
                self.fields['volunteer_calendar'].queryset = VolunteerCalendar.objects.select_related('volunteer').all()
            else:
                try:
                    volunteer = user.volunteer_profile
                    if volunteer.role in ['ADMIN', 'EMPLOYEE']:
                        # Les admins et employés voient tous les calendriers
                        self.fields['volunteer_calendar'].queryset = VolunteerCalendar.objects.select_related('volunteer').all()
                    elif volunteer.role == 'VOLUNTEER_INTERVIEW':
                        # Les bénévoles d'entretien voient tous les calendriers mais ne peuvent modifier que le leur
                        self.fields['volunteer_calendar'].queryset = VolunteerCalendar.objects.select_related('volunteer').all()
                        # Pré-sélectionner leur propre calendrier
                        user_calendar = VolunteerCalendar.objects.filter(volunteer=volunteer).first()
                        if user_calendar:
                            self.fields['volunteer_calendar'].initial = user_calendar
                    else:
                        # Autres rôles : seulement leur calendrier
                        self.fields['volunteer_calendar'].queryset = VolunteerCalendar.objects.filter(volunteer=volunteer)
                except AttributeError:
                    # Utilisateur sans profil volunteer
                    self.fields['volunteer_calendar'].queryset = VolunteerCalendar.objects.none()

        # Pré-remplir avec les données GET si disponibles
        if hasattr(self, 'initial'):
            # Auto-remplir le bénéficiaire si fourni en paramètre
            beneficiary_param = self.initial.get('beneficiary')
            if beneficiary_param:
                try:
                    if isinstance(beneficiary_param, str):
                        beneficiary_id = int(beneficiary_param)
                        # Utiliser directement l'ID, pas l'objet
                        self.fields['beneficiary'].initial = beneficiary_id
                    else:
                        self.fields['beneficiary'].initial = beneficiary_param
                except (ValueError, TypeError):
                    pass

            # Auto-remplir la date si fournie en paramètre
            date_param = self.initial.get('date')
            if date_param:
                try:
                    if isinstance(date_param, str):
                        date_obj = datetime.strptime(date_param, '%Y-%m-%d').date()
                    else:
                        date_obj = date_param
                    self.fields['appointment_date'].initial = date_obj
                except (ValueError, TypeError):
                    pass

            # Auto-remplir l'heure si fournie en paramètre
            time_param = self.initial.get('time')
            start_time_param = self.initial.get('start_time')
            end_time_param = self.initial.get('end_time')

            if start_time_param:
                try:
                    if isinstance(start_time_param, str):
                        start_time_obj = datetime.strptime(start_time_param, '%H:%M').time()
                    else:
                        start_time_obj = start_time_param
                    self.fields['start_time'].initial = start_time_obj
                except (ValueError, TypeError):
                    pass

            if end_time_param:
                try:
                    if isinstance(end_time_param, str):
                        end_time_obj = datetime.strptime(end_time_param, '%H:%M').time()
                    else:
                        end_time_obj = end_time_param
                    self.fields['end_time'].initial = end_time_obj
                except (ValueError, TypeError):
                    pass

            elif time_param:
                try:
                    if isinstance(time_param, str):
                        time_obj = datetime.strptime(time_param, '%H:%M').time()
                    else:
                        time_obj = time_param
                    self.fields['start_time'].initial = time_obj
                    # Proposer une heure de fin 1h plus tard
                    end_datetime = datetime.combine(datetime.today(), time_obj) + timedelta(hours=1)
                    self.fields['end_time'].initial = end_datetime.time()
                except (ValueError, TypeError):
                    pass

            # Auto-remplir le calendrier bénévole si fourni en paramètre
            volunteer_calendar_param = self.initial.get('volunteer_calendar')
            if volunteer_calendar_param:
                try:
                    if isinstance(volunteer_calendar_param, str):
                        calendar_id = int(volunteer_calendar_param)
                        self.fields['volunteer_calendar'].initial = calendar_id
                    else:
                        self.fields['volunteer_calendar'].initial = volunteer_calendar_param
                except (ValueError, TypeError):
                    pass

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        appointment_date = cleaned_data.get('appointment_date')
        volunteer_calendar = cleaned_data.get('volunteer_calendar')

        # Vérifier que l'heure de fin est après l'heure de début
        if start_time and end_time:
            if end_time <= start_time:
                raise forms.ValidationError("L'heure de fin doit être après l'heure de début.")

        # Vérifier que la date n'est pas dans le passé
        if appointment_date:
            if appointment_date < timezone.now().date():
                raise forms.ValidationError("Impossible de planifier un rendez-vous dans le passé.")

        # Vérifier les conflits de rendez-vous si on a toutes les données
        if volunteer_calendar and appointment_date and start_time and end_time:
            start_datetime = datetime.combine(appointment_date, start_time)
            end_datetime = datetime.combine(appointment_date, end_time)

            # Exclure le rendez-vous actuel si on est en modification
            conflicting_appointments = Appointment.objects.filter(
                volunteer_calendar=volunteer_calendar,
                appointment_date=appointment_date,
                start_time__lt=end_time,
                end_time__gt=start_time
            )

            if self.instance.pk:
                conflicting_appointments = conflicting_appointments.exclude(pk=self.instance.pk)

            if conflicting_appointments.exists():
                raise forms.ValidationError(
                    f"Conflit détecté avec un autre rendez-vous de {volunteer_calendar.volunteer.get_full_name()}."
                )

        return cleaned_data


class AvailabilitySlotForm(forms.ModelForm):
    class Meta:
        model = AvailabilitySlot
        fields = [
            'title', 'slot_type', 'recurrence_type', 'weekday',
            'specific_date', 'start_time', 'end_time', 'notes'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'slot_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'recurrence_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'weekday': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'specific_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        recurrence_type = cleaned_data.get('recurrence_type')
        weekday = cleaned_data.get('weekday')
        specific_date = cleaned_data.get('specific_date')

        # Vérifier que l'heure de fin est après l'heure de début
        if start_time and end_time:
            if end_time <= start_time:
                raise forms.ValidationError("L'heure de fin doit être après l'heure de début.")

        # Vérifier les champs requis selon le type de récurrence
        if recurrence_type == 'WEEKLY' and not weekday:
            raise forms.ValidationError("Le jour de la semaine est requis pour une récurrence hebdomadaire.")

        if recurrence_type == 'ONCE' and not specific_date:
            raise forms.ValidationError("La date spécifique est requise pour un créneau unique.")

        return cleaned_data