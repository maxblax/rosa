"""Services aux bénéficiaires : catalogue, inscriptions, distributions et aides financières.

Trois mécanismes :
- distributions (épicerie, vestiaire...) : un service a des sessions datées
  (ex : mercredi après-midi) avec une jauge éventuelle ; une inscription
  réserve une ou plusieurs sessions avec la composition de la famille, puis
  la présence ou l'absence est pointée ;
- aide financière : demande instruite en entretien, validée ou refusée par
  un administrateur, puis versement suivi par un administrateur ;
- service simple / orientation (interne ou externe), avec un bon imprimable.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Service(models.Model):
    KIND_DISTRIBUTION = 'DISTRIBUTION'
    KIND_FINANCIAL = 'FINANCIAL'
    KIND_SIMPLE = 'SIMPLE'
    KIND_CHOICES = [
        (KIND_DISTRIBUTION, 'Distribution sur sessions datées (épicerie, vestiaire...)'),
        (KIND_FINANCIAL, 'Aide financière (validation par un administrateur)'),
        (KIND_SIMPLE, 'Service simple / orientation'),
    ]

    CATEGORY_INTERNAL = 'INTERNAL'
    CATEGORY_SUPPORT = 'SUPPORT'
    CATEGORY_EXTERNAL = 'EXTERNAL'
    CATEGORY_CHOICES = [
        (CATEGORY_INTERNAL, 'Orientation interne'),
        (CATEGORY_SUPPORT, 'Soutien'),
        (CATEGORY_EXTERNAL, 'Orientation externe'),
    ]

    CAPACITY_FAMILIES = 'FAMILIES'
    CAPACITY_PERSONS = 'PERSONS'
    CAPACITY_UNIT_CHOICES = [
        (CAPACITY_FAMILIES, 'Familles'),
        (CAPACITY_PERSONS, 'Personnes'),
    ]

    WEEKDAY_CHOICES = [
        (0, 'Lundi'), (1, 'Mardi'), (2, 'Mercredi'), (3, 'Jeudi'),
        (4, 'Vendredi'), (5, 'Samedi'), (6, 'Dimanche'),
    ]

    name = models.CharField('Nom', max_length=150)
    description = models.TextField('Description', blank=True)
    kind = models.CharField('Fonctionnement', max_length=20, choices=KIND_CHOICES, default=KIND_SIMPLE)
    category = models.CharField('Catégorie', max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_INTERNAL)
    partner = models.ForeignKey('partners.Partner', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='beneficiary_services', verbose_name='Partenaire')
    requires_details = models.BooleanField(
        'Précision obligatoire', default=False,
        help_text='Le bénévole doit écrire une précision en toutes lettres (ex : « Autre »).')
    is_active = models.BooleanField('Actif', default=True)
    order = models.PositiveIntegerField('Ordre d\'affichage', default=100)

    # Distributions (les créneaux récurrents sont dans ServiceScheduleSlot)
    default_tickets = models.PositiveIntegerField(
        'Passages par inscription', default=1,
        help_text='Nombre de tickets donnés à chaque inscription (ex : 3 pour l\'épicerie, 1 pour le vestiaire).')
    max_bookings_per_week = models.PositiveIntegerField(
        'Passages max par semaine', null=True, blank=True, help_text='Vide = pas de limite.')
    session_capacity = models.PositiveIntegerField('Jauge par défaut', null=True, blank=True,
                                                   help_text='Vide = pas de limite.')
    capacity_unit = models.CharField('Unité de la jauge', max_length=10, choices=CAPACITY_UNIT_CHOICES,
                                     default=CAPACITY_FAMILIES)
    max_adults_per_booking = models.PositiveIntegerField('Adultes max par date', null=True, blank=True)
    max_children_per_booking = models.PositiveIntegerField('Enfants max par date (bébés inclus)',
                                                           null=True, blank=True)

    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)

    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    @property
    def is_distribution(self):
        return self.kind == self.KIND_DISTRIBUTION

    @property
    def is_financial(self):
        return self.kind == self.KIND_FINANCIAL

    @property
    def is_simple(self):
        return self.kind == self.KIND_SIMPLE



class ServiceScheduleSlot(models.Model):
    """Créneau récurrent hebdomadaire d'un service (ex : épicerie le mardi 14h-17h)."""
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='schedule_slots',
                                verbose_name='Service')
    weekday = models.PositiveSmallIntegerField('Jour', choices=Service.WEEKDAY_CHOICES)
    start_time = models.TimeField('Début', null=True, blank=True)
    end_time = models.TimeField('Fin', null=True, blank=True)
    capacity = models.PositiveIntegerField('Jauge', null=True, blank=True, help_text='Vide = pas de limite.')
    is_active = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Créneau récurrent'
        verbose_name_plural = 'Créneaux récurrents'
        ordering = ['weekday', 'start_time']

    def __str__(self):
        hours = f" {self.start_time:%H:%M}" if self.start_time else ''
        return f"{self.service.name} - {self.get_weekday_display()}{hours}"


class ServiceSession(models.Model):
    """Occurrence datée d'un service de distribution.

    Les sessions sont générées à partir des créneaux récurrents. Chacune peut
    ensuite être modifiée seule (date, heure, jauge), annulée, ou ajoutée
    ponctuellement sans créneau récurrent.
    """
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='sessions', verbose_name='Service')
    schedule_slot = models.ForeignKey(ServiceScheduleSlot, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='sessions', verbose_name='Créneau récurrent')
    original_date = models.DateField('Date prévue par le planning', null=True, blank=True)
    date = models.DateField('Date')
    start_time = models.TimeField('Début', null=True, blank=True)
    end_time = models.TimeField('Fin', null=True, blank=True)
    capacity = models.PositiveIntegerField('Jauge', null=True, blank=True)
    is_closed = models.BooleanField('Annulée', default=False)
    is_customized = models.BooleanField('Modifiée à la main', default=False)
    notes = models.TextField('Notes', blank=True)

    class Meta:
        verbose_name = 'Session'
        verbose_name_plural = 'Sessions'
        ordering = ['date', 'start_time']
        constraints = [
            models.UniqueConstraint(fields=['schedule_slot', 'original_date'], name='unique_session_per_slot_date'),
        ]

    def __str__(self):
        hours = f" {self.start_time:%H:%M}" if self.start_time else ''
        return f"{self.service.name} - {self.date:%d/%m/%Y}{hours}"

    def active_bookings(self):
        return self.bookings.exclude(registration__status=ServiceRegistration.STATUS_CANCELLED)

    @property
    def load(self):
        """Occupation dans l'unité de la jauge du service."""
        bookings = self.active_bookings()
        if self.service.capacity_unit == Service.CAPACITY_PERSONS:
            return sum(b.persons for b in bookings)
        return bookings.count()

    @property
    def remaining(self):
        if self.capacity is None:
            return None
        return max(self.capacity - self.load, 0)

    def can_accept(self, persons=1):
        if self.is_closed:
            return False
        if self.capacity is None:
            return True
        needed = persons if self.service.capacity_unit == Service.CAPACITY_PERSONS else 1
        return self.load + needed <= self.capacity


class ServiceRegistration(models.Model):
    """Inscription / orientation d'un bénéficiaire (sa famille) à un service."""
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_DONE = 'DONE'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'En cours'),
        (STATUS_DONE, 'Terminé'),
        (STATUS_CANCELLED, 'Annulé'),
    ]

    beneficiary = models.ForeignKey('beneficiaries.Beneficiary', on_delete=models.CASCADE,
                                    related_name='service_registrations', verbose_name='Bénéficiaire')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='registrations',
                                verbose_name='Service')
    interaction = models.ForeignKey('beneficiaries.Interaction', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='service_registrations', verbose_name='Entretien d\'origine')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='service_registrations', verbose_name='Inscrit par')
    status = models.CharField('Statut', max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    tickets = models.PositiveIntegerField('Passages accordés', default=1)
    details = models.TextField('Précisions', blank=True)
    partner_name = models.CharField('Partenaire (texte libre)', max_length=200, blank=True)

    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)

    class Meta:
        verbose_name = 'Inscription à un service'
        verbose_name_plural = 'Inscriptions aux services'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.service.name} - {self.beneficiary}"

    @property
    def partner_label(self):
        if self.partner_name:
            return self.partner_name
        return self.service.partner.name if self.service.partner else ''

    @property
    def tickets_used(self):
        return self.bookings.count()

    @property
    def tickets_left(self):
        return max(self.tickets - self.tickets_used, 0)

    def refresh_status(self):
        """Termine l'inscription quand tous ses passages sont réservés et pointés."""
        if self.status == self.STATUS_CANCELLED or not self.service.is_distribution:
            return
        bookings = list(self.bookings.all())
        done = (len(bookings) >= self.tickets and all(b.attended is not None for b in bookings))
        new_status = self.STATUS_DONE if done else self.STATUS_ACTIVE
        if new_status != self.status:
            self.status = new_status
            self.save(update_fields=['status', 'updated_at'])


class ServiceBooking(models.Model):
    """Réservation d'une famille sur une session, puis présence / absence."""
    registration = models.ForeignKey(ServiceRegistration, on_delete=models.CASCADE, related_name='bookings',
                                     verbose_name='Inscription')
    session = models.ForeignKey(ServiceSession, on_delete=models.PROTECT, related_name='bookings',
                                verbose_name='Session')
    adults = models.PositiveIntegerField('Adultes', default=1)
    children = models.PositiveIntegerField('Enfants', default=0)
    babies = models.PositiveIntegerField('Bébés', default=0)
    attended = models.BooleanField('Présent', null=True, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='recorded_service_bookings', verbose_name='Pointé par')
    recorded_at = models.DateTimeField('Pointé le', null=True, blank=True)
    observations = models.CharField('Observations', max_length=300, blank=True)

    class Meta:
        verbose_name = 'Réservation'
        verbose_name_plural = 'Réservations'
        ordering = ['session__date', 'session__start_time']
        constraints = [
            models.UniqueConstraint(fields=['registration', 'session'], name='unique_booking_per_session'),
        ]

    def __str__(self):
        return f"{self.registration.beneficiary} - {self.session}"

    @property
    def persons(self):
        return self.adults + self.children + self.babies

    @property
    def beneficiary(self):
        return self.registration.beneficiary

    def mark(self, attended, user=None):
        self.attended = attended
        self.recorded_by = user
        self.recorded_at = timezone.now() if attended is not None else None
        self.save(update_fields=['attended', 'recorded_by', 'recorded_at'])
        self.registration.refresh_status()


class FinancialAidRequest(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_PAID = 'PAID'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'En attente de validation'),
        (STATUS_APPROVED, 'Validée'),
        (STATUS_REJECTED, 'Refusée'),
        (STATUS_PAID, 'Versée'),
    ]

    NATURE_CHOICES = [
        ('CANTINE_SCOLARITE', 'Cantine / scolarité'),
        ('TRANSPORT', 'Transport'),
        ('OPTIQUE', 'Optique'),
        ('ASSURANCE_HABITATION', 'Assurance habitation'),
        ('TIMBRES_FISCAUX', 'Timbres fiscaux'),
        ('SANTE', 'Santé'),
        ('ENERGIE', 'Énergie'),
        ('AUTRE', 'Autre'),
    ]

    PAYMENT_CHOICES = [
        ('CASH', 'Espèces'),
        ('CHECK', 'Chèque'),
        ('TRANSFER', 'Virement'),
        ('CARD', 'Carte / ticket prépayé'),
        ('DIRECT', 'Paiement direct au fournisseur'),
        ('OTHER', 'Autre'),
    ]

    beneficiary = models.ForeignKey('beneficiaries.Beneficiary', on_delete=models.CASCADE,
                                    related_name='financial_aid_requests', verbose_name='Bénéficiaire')
    interaction = models.ForeignKey('beneficiaries.Interaction', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='financial_aid_requests', verbose_name='Entretien d\'origine')
    amount = models.DecimalField('Montant (€)', max_digits=10, decimal_places=2)
    nature = models.CharField('Nature', max_length=30, choices=NATURE_CHOICES, default='AUTRE')
    reason = models.TextField('Motif', help_text='En toutes lettres : carte de bus, cantine de mars...')
    status = models.CharField('Statut', max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='financial_aid_requests', verbose_name='Demandée par')
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='financial_aid_decisions', verbose_name='Décidée par')
    decided_at = models.DateTimeField('Décidée le', null=True, blank=True)
    rejection_reason = models.TextField('Motif du refus', blank=True)

    paid_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='financial_aid_payments', verbose_name='Versement saisi par')
    paid_at = models.DateField('Versée le', null=True, blank=True)
    payment_method = models.CharField('Moyen de versement', max_length=20, choices=PAYMENT_CHOICES, blank=True)
    payment_notes = models.TextField('Notes de versement', blank=True)

    created_at = models.DateTimeField('Créée le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifiée le', auto_now=True)

    class Meta:
        verbose_name = 'Demande d\'aide financière'
        verbose_name_plural = 'Demandes d\'aide financière'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.amount} € - {self.beneficiary} ({self.get_status_display()})"

    @property
    def badge_classes(self):
        return {
            self.STATUS_PENDING: 'bg-yellow-100 text-yellow-800',
            self.STATUS_APPROVED: 'bg-blue-100 text-blue-800',
            self.STATUS_REJECTED: 'bg-red-100 text-red-800',
            self.STATUS_PAID: 'bg-green-100 text-green-800',
        }.get(self.status, 'bg-gray-100 text-gray-800')
