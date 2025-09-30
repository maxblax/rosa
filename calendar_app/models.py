from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta, time
import calendar

class VolunteerCalendar(models.Model):
    """
    Calendrier personnel de chaque bénévole.
    Contient les paramètres et préférences d'affichage.
    """

    volunteer = models.OneToOneField(
        'volunteers.Volunteer',
        on_delete=models.CASCADE,
        related_name='calendar',
        verbose_name='Bénévole'
    )

    # Paramètres du calendrier
    default_view = models.CharField(
        max_length=10,
        choices=[
            ('day', 'Vue jour'),
            ('week', 'Vue semaine'),
            ('month', 'Vue mois'),
        ],
        default='week',
        verbose_name='Vue par défaut'
    )

    work_start_time = models.TimeField(
        default=time(8, 0),
        verbose_name='Début de journée'
    )

    work_end_time = models.TimeField(
        default=time(18, 0),
        verbose_name='Fin de journée'
    )

    show_weekends = models.BooleanField(
        default=False,
        verbose_name='Afficher les week-ends'
    )

    email_reminders = models.BooleanField(
        default=True,
        verbose_name='Rappels par email'
    )

    reminder_hours_before = models.IntegerField(
        default=24,
        verbose_name='Rappel (heures avant)'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Calendrier bénévole'
        verbose_name_plural = 'Calendriers bénévoles'

    def clean(self):
        # Vérifier que le bénévole a le droit d'avoir un calendrier
        if (self.volunteer and
            self.volunteer.role == 'VOLUNTEER_GOVERNANCE'):
            raise ValidationError('Les bénévoles de gouvernance n\'ont pas accès au calendrier.')

    def __str__(self):
        return f"{self.volunteer.user.get_full_name()}"


class AvailabilitySlot(models.Model):
    """
    Créneaux de disponibilité des bénévoles.
    Un créneau peut être récurrent (ex: tous les lundis 14h-16h)
    ou ponctuel (ex: le 15 mars 10h-12h).
    """

    WEEKDAY_CHOICES = [
        (0, 'Lundi'),
        (1, 'Mardi'),
        (2, 'Mercredi'),
        (3, 'Jeudi'),
        (4, 'Vendredi'),
        (5, 'Samedi'),
        (6, 'Dimanche'),
    ]

    RECURRENCE_CHOICES = [
        ('NONE', 'Ponctuel'),
        ('WEEKLY', 'Hebdomadaire'),
        ('BIWEEKLY', 'Toutes les 2 semaines'),
        ('MONTHLY', 'Mensuel'),
    ]

    SLOT_TYPES = [
        ('AVAILABILITY', 'Disponibilité'),
        ('BUSY', 'Occupé'),
        ('UNAVAILABLE', 'Indisponible'),
    ]

    volunteer_calendar = models.ForeignKey(
        VolunteerCalendar,
        on_delete=models.CASCADE,
        related_name='availability_slots'
    )

    # Type et récurrence
    slot_type = models.CharField(
        max_length=15,
        choices=SLOT_TYPES,
        default='AVAILABILITY',
        verbose_name='Type de créneau'
    )

    recurrence_type = models.CharField(
        max_length=10,
        choices=RECURRENCE_CHOICES,
        default='WEEKLY',
        verbose_name='Type de récurrence'
    )

    # Pour récurrence hebdomadaire/bi-hebdomadaire
    weekday = models.IntegerField(
        choices=WEEKDAY_CHOICES,
        null=True, blank=True,
        verbose_name='Jour de la semaine'
    )

    # Pour créneaux ponctuels
    specific_date = models.DateField(
        null=True, blank=True,
        verbose_name='Date spécifique'
    )

    # Horaires
    start_time = models.TimeField(verbose_name='Heure de début')
    end_time = models.TimeField(verbose_name='Heure de fin')

    # Période de validité pour récurrences
    valid_from = models.DateField(
        default=timezone.now,
        verbose_name='Valide à partir du'
    )
    valid_until = models.DateField(
        null=True, blank=True,
        verbose_name='Valide jusqu\'au'
    )

    # Métadonnées
    title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Titre du créneau'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Notes'
    )

    is_bookable = models.BooleanField(
        default=True,
        verbose_name='Peut être réservé'
    )

    max_appointments = models.PositiveIntegerField(
        default=1,
        verbose_name='Nombre max de RDV'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Actif'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_availability_slots'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Créneau de disponibilité'
        verbose_name_plural = 'Créneaux de disponibilité'
        ordering = ['weekday', 'start_time']

    def clean(self):
        """Validation du modèle"""
        if self.start_time >= self.end_time:
            raise ValidationError('L\'heure de fin doit être après l\'heure de début.')

        if self.recurrence_type != 'NONE' and not self.weekday:
            raise ValidationError('Le jour de la semaine est requis pour les récurrences.')

        if self.recurrence_type == 'NONE' and not self.specific_date:
            raise ValidationError('La date spécifique est requise pour un créneau ponctuel.')

        # Vérifier que le bénévole a le droit d'avoir un calendrier
        if (self.volunteer_calendar and
            self.volunteer_calendar.volunteer.role == 'VOLUNTEER_GOVERNANCE'):
            raise ValidationError('Les bénévoles de gouvernance ne peuvent pas avoir de créneaux.')

    def __str__(self):
        if self.recurrence_type == 'NONE':
            return f"{self.volunteer_calendar.volunteer.user.get_full_name()} - {self.specific_date} {self.start_time}-{self.end_time}"
        else:
            weekday_name = dict(self.WEEKDAY_CHOICES)[self.weekday]
            return f"{self.volunteer_calendar.volunteer.user.get_full_name()} - {weekday_name} {self.start_time}-{self.end_time}"

    @property
    def current_appointments_count(self):
        """Nombre actuel de RDV sur ce créneau"""
        return self.appointments.filter(
            status__in=['SCHEDULED', 'CONFIRMED']
        ).count()

    @property
    def is_available_for_booking(self):
        """Vérifie si ce créneau peut encore accepter des RDV"""
        return (self.is_bookable and
                self.slot_type == 'AVAILABILITY' and
                self.current_appointments_count < self.max_appointments)

    @property
    def duration_hours(self):
        """Durée du créneau en heures"""
        start_dt = datetime.combine(timezone.now().date(), self.start_time)
        end_dt = datetime.combine(timezone.now().date(), self.end_time)
        return (end_dt - start_dt).total_seconds() / 3600

    def get_occurrences_in_range(self, start_date, end_date):
        """
        Retourne toutes les occurrences de ce créneau dans une plage de dates.
        """
        occurrences = []

        if self.recurrence_type == 'NONE':
            # Créneau ponctuel
            if start_date <= self.specific_date <= end_date:
                occurrences.append({
                    'date': self.specific_date,
                    'start_time': self.start_time,
                    'end_time': self.end_time,
                    'slot': self
                })
        else:
            # Créneaux récurrents
            current_date = max(start_date, self.valid_from)
            end_check = min(end_date, self.valid_until) if self.valid_until else end_date

            while current_date <= end_check:
                if current_date.weekday() == self.weekday:
                    occurrences.append({
                        'date': current_date,
                        'start_time': self.start_time,
                        'end_time': self.end_time,
                        'slot': self
                    })

                    if self.recurrence_type == 'WEEKLY':
                        current_date += timedelta(days=7)
                    elif self.recurrence_type == 'BIWEEKLY':
                        current_date += timedelta(days=14)
                    elif self.recurrence_type == 'MONTHLY':
                        # Ajouter un mois (approximatif)
                        month = current_date.month
                        year = current_date.year
                        if month == 12:
                            month = 1
                            year += 1
                        else:
                            month += 1
                        try:
                            current_date = current_date.replace(month=month, year=year)
                        except ValueError:
                            # Gérer les fins de mois (31 → 28/29/30)
                            current_date = current_date.replace(month=month, year=year, day=1)
                            current_date = current_date.replace(day=min(current_date.day,
                                calendar.monthrange(year, month)[1]))
                    else:
                        current_date += timedelta(days=1)
                else:
                    current_date += timedelta(days=1)

        return occurrences


class AvailabilityException(models.Model):
    """
    Exceptions aux créneaux de disponibilité récurrents.
    Permet de modifier/supprimer une occurrence spécifique d'un créneau récurrent.
    """

    EXCEPTION_TYPES = [
        ('CANCELLED', 'Annulé'),
        ('MODIFIED', 'Modifié'),
        ('MOVED', 'Déplacé'),
    ]

    availability_slot = models.ForeignKey(
        AvailabilitySlot,
        on_delete=models.CASCADE,
        related_name='exceptions'
    )

    exception_date = models.DateField(
        verbose_name='Date d\'exception'
    )

    exception_type = models.CharField(
        max_length=10,
        choices=EXCEPTION_TYPES,
        verbose_name='Type d\'exception'
    )

    # Pour les modifications
    new_start_time = models.TimeField(
        null=True, blank=True,
        verbose_name='Nouvelle heure de début'
    )
    new_end_time = models.TimeField(
        null=True, blank=True,
        verbose_name='Nouvelle heure de fin'
    )
    new_date = models.DateField(
        null=True, blank=True,
        verbose_name='Nouvelle date'
    )

    reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Raison'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        verbose_name = 'Exception de disponibilité'
        verbose_name_plural = 'Exceptions de disponibilité'
        unique_together = ['availability_slot', 'exception_date']

    def __str__(self):
        return f"Exception {self.get_exception_type_display()} - {self.exception_date}"


class Appointment(models.Model):
    """
    Rendez-vous entre un bénévole et un bénéficiaire.
    """

    STATUS_CHOICES = [
        ('SCHEDULED', 'Programmé'),
        ('CONFIRMED', 'Confirmé'),
        ('IN_PROGRESS', 'En cours'),
        ('COMPLETED', 'Terminé'),
        ('CANCELLED', 'Annulé'),
        ('NO_SHOW', 'Absent'),
    ]

    APPOINTMENT_TYPES = [
        ('INTERVIEW', 'Entretien'),
        ('FOLLOW_UP', 'Suivi'),
        ('ADMINISTRATIVE', 'Aide administrative'),
        ('SOCIAL', 'Accompagnement social'),
        ('OTHER', 'Autre'),
    ]

    # Participants
    volunteer_calendar = models.ForeignKey(
        VolunteerCalendar,
        on_delete=models.CASCADE,
        related_name='appointments',
        null=True,
        blank=True,
        verbose_name='Bénévole assigné'
    )

    beneficiary = models.ForeignKey(
        'beneficiaries.Beneficiary',
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name='Bénéficiaire'
    )

    # Timing
    appointment_date = models.DateField(verbose_name='Date du rendez-vous')
    start_time = models.TimeField(verbose_name='Heure de début')
    end_time = models.TimeField(verbose_name='Heure de fin')

    # Détails
    appointment_type = models.CharField(
        max_length=15,
        choices=APPOINTMENT_TYPES,
        default='INTERVIEW',
        verbose_name='Type de rendez-vous'
    )

    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Objet du rendez-vous'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )

    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Lieu'
    )

    # Statut
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default='SCHEDULED',
        verbose_name='Statut'
    )

    # Notes
    preparation_notes = models.TextField(
        blank=True,
        verbose_name='Notes de préparation'
    )

    completion_notes = models.TextField(
        blank=True,
        verbose_name='Notes de compte-rendu'
    )

    # Lien optionnel vers un créneau de disponibilité
    availability_slot = models.ForeignKey(
        AvailabilitySlot,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='appointments',
        verbose_name='Créneau de disponibilité'
    )

    # Métadonnées
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_appointments'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rendez-vous'
        verbose_name_plural = 'Rendez-vous'
        ordering = ['appointment_date', 'start_time']

    def clean(self):
        """Validation du modèle"""
        if self.start_time >= self.end_time:
            raise ValidationError('L\'heure de fin doit être après l\'heure de début.')

        # Vérifier que le bénévole peut avoir des RDV
        if (self.volunteer_calendar and
            self.volunteer_calendar.volunteer.role == 'VOLUNTEER_GOVERNANCE'):
            raise ValidationError('Les bénévoles de gouvernance ne peuvent pas avoir de rendez-vous.')

        # Vérifier que le RDV est dans le futur (sauf si modification)
        if self.appointment_date and self.appointment_date < timezone.now().date():
            if not self.pk:  # Nouveau RDV
                raise ValidationError('Impossible de créer un rendez-vous dans le passé.')

    def __str__(self):
        if self.volunteer_calendar:
            volunteer_name = self.volunteer_calendar.volunteer.user.get_full_name()
        else:
            volunteer_name = "Sans bénévole assigné"
        beneficiary_name = f"{self.beneficiary.first_name} {self.beneficiary.last_name}"
        return f"{volunteer_name} → {beneficiary_name} - {self.appointment_date} {self.start_time}"

    @property
    def volunteer(self):
        """Raccourci vers le bénévole"""
        return self.volunteer_calendar.volunteer if self.volunteer_calendar else None

    @property
    def duration_hours(self):
        """Durée du rendez-vous en heures"""
        start_dt = datetime.combine(self.appointment_date, self.start_time)
        end_dt = datetime.combine(self.appointment_date, self.end_time)
        return (end_dt - start_dt).total_seconds() / 3600

    @property
    def is_past(self):
        """Indique si le rendez-vous est passé"""
        now = timezone.now()
        appointment_datetime = datetime.combine(self.appointment_date, self.end_time)
        return appointment_datetime.replace(tzinfo=timezone.get_current_timezone()) < now

    @property
    def is_today(self):
        """Indique si le rendez-vous est aujourd'hui"""
        return self.appointment_date == timezone.now().date()

    def can_be_modified_by(self, user):
        """Vérifie si l'utilisateur peut modifier ce rendez-vous"""
        if not user.is_authenticated:
            return False

        # Admin et salariés peuvent tout modifier
        if (user.is_superuser or
            (hasattr(user, 'volunteer_profile') and
             user.volunteer_profile.role in ['ADMIN', 'EMPLOYEE'])):
            return True

        # Le bénévole concerné peut modifier ses propres RDV
        if (hasattr(user, 'volunteer_profile') and
            user.volunteer_profile == self.volunteer):
            return True

        # Créateur du RDV peut le modifier
        if user == self.created_by:
            return True

        return False


# Signaux pour créer automatiquement les calendriers
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender='volunteers.Volunteer')
def create_volunteer_calendar(sender, instance, created, **kwargs):
    """Crée automatiquement un calendrier pour chaque nouveau bénévole éligible"""
    if created and instance.role != 'VOLUNTEER_GOVERNANCE':
        # Créer le calendrier uniquement si le bénévole peut en avoir un
        VolunteerCalendar.objects.get_or_create(
            volunteer=instance
        )