from django.db import models
from django.urls import reverse


class Partner(models.Model):
    """Modèle pour les partenaires de l'association"""

    # Informations principales
    name = models.CharField('Nom du partenaire', max_length=200)

    # Coordonnées
    address = models.TextField('Adresse', blank=True)
    phone = models.CharField('Téléphone', max_length=20, blank=True)
    email = models.EmailField('Email', blank=True)

    # Services (stockés sous forme de liste séparée par des virgules)
    services = models.TextField(
        'Services fournis',
        blank=True,
        help_text='Services séparés par des virgules'
    )

    # Métadonnées
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)

    class Meta:
        verbose_name = 'Partenaire'
        verbose_name_plural = 'Partenaires'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('partners:detail', kwargs={'pk': self.pk})

    def get_services_list(self):
        """Retourne les services sous forme de liste"""
        if not self.services:
            return []
        return [s.strip() for s in self.services.split(',') if s.strip()]

    def set_services_list(self, services_list):
        """Définit les services à partir d'une liste"""
        self.services = ', '.join(services_list)
