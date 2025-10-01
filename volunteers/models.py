from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date


class Volunteer(models.Model):
    """Modèle pour les bénévoles de l'association avec gestion des rôles RBAC"""

    ROLE_CHOICES = [
        ('ADMIN', 'Administrateur'),
        ('EMPLOYEE', 'Salarié'),
        ('VOLUNTEER_INTERVIEW', 'Bénévole Entretien'),
        ('VOLUNTEER_GOVERNANCE', 'Bénévole Gouvernance'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Actif'),
        ('INACTIVE', 'Inactif'),
        ('SUSPENDED', 'Suspendu'),
    ]

    CIVILITY_CHOICES = [
        ('M', 'M.'),
        ('MME', 'Mme'),
        ('AUTRE', 'Autre'),
    ]

    # Relation avec l'utilisateur Django
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='volunteer_profile',
        verbose_name='Utilisateur'
    )

    # Informations personnelles
    civility = models.CharField('Civilité', max_length=10, choices=CIVILITY_CHOICES, blank=True)
    birth_date = models.DateField('Date de naissance', null=True, blank=True)
    phone = models.CharField('Téléphone', max_length=20, blank=True)

    # Adresse
    address = models.TextField('Adresse', blank=True)

    # Rôle et statut
    role = models.CharField(
        'Rôle',
        max_length=30,
        choices=ROLE_CHOICES,
        default='VOLUNTEER_INTERVIEW',
        help_text='Détermine les permissions d\'accès dans l\'application'
    )
    status = models.CharField(
        'Statut',
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )

    # Informations professionnelles
    skills = models.TextField(
        'Compétences/Savoir-faire',
        blank=True,
        help_text='Compétences particulières du bénévole'
    )

    # Dates importantes
    join_date = models.DateField('Date d\'adhésion', default=date.today)
    last_activity = models.DateTimeField('Dernière activité', null=True, blank=True)

    # Métadonnées
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)

    class Meta:
        verbose_name = 'Bénévole'
        verbose_name_plural = 'Bénévoles'
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        civility_display = self.get_civility_display() if self.civility else ''
        return f"{civility_display} {self.user.first_name} {self.user.last_name}".strip()

    def get_absolute_url(self):
        return reverse('volunteers:detail', kwargs={'pk': self.pk})

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def age(self):
        """Calcule l'âge du bénévole"""
        if not self.birth_date:
            return None
        today = date.today()
        age = today.year - self.birth_date.year
        if today.month < self.birth_date.month or (today.month == self.birth_date.month and today.day < self.birth_date.day):
            age -= 1
        return age

    @property
    def is_admin(self):
        """Vérifie si le bénévole a les droits d'administrateur"""
        return self.role == 'ADMIN'

    @property
    def is_employee(self):
        """Vérifie si c'est un salarié"""
        return self.role == 'EMPLOYEE'

    @property
    def can_modify_beneficiaries(self):
        """Vérifie si le bénévole peut modifier les dossiers bénéficiaires"""
        return self.role in ['ADMIN', 'EMPLOYEE', 'VOLUNTEER_INTERVIEW']

    @property
    def can_view_reports_only(self):
        """Vérifie si le bénévole n'a accès qu'aux rapports"""
        return self.role == 'VOLUNTEER_GOVERNANCE'

    @property
    def can_manage_users(self):
        """Vérifie si le bénévole peut créer/modifier/supprimer des utilisateurs"""
        return self.role in ['ADMIN', 'EMPLOYEE']

    @property
    def role_icon(self):
        """Retourne l'icône FontAwesome appropriée selon le rôle"""
        icons = {
            'ADMIN': 'fas fa-crown',
            'EMPLOYEE': 'fas fa-briefcase',
            'VOLUNTEER_INTERVIEW': 'fas fa-users',
            'VOLUNTEER_GOVERNANCE': 'fas fa-chart-bar',
        }
        return icons.get(self.role, 'fas fa-user')



