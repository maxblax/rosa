from django.db import models
from django.urls import reverse


class News(models.Model):
    """Modèle pour les actualités et événements de l'association"""

    NEWS_TYPE_CHOICES = [
        ('EVENEMENT', 'Événement'),
        ('PARTENARIAT', 'Partenariat'),
        ('FORMATION', 'Formation'),
        ('INFO', 'Information'),
        ('AUTRE', 'Autre'),
    ]

    # Informations principales
    title = models.CharField('Titre', max_length=200)
    news_type = models.CharField(
        'Type',
        max_length=20,
        choices=NEWS_TYPE_CHOICES,
        default='INFO'
    )
    description = models.TextField('Description')

    # Date de publication
    publication_date = models.DateField('Date de publication', auto_now_add=True)

    # Option pour mettre en avant une actualité
    is_pinned = models.BooleanField('Épinglé', default=False, help_text='Afficher en premier')

    # Métadonnées
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)

    class Meta:
        verbose_name = 'Actualité'
        verbose_name_plural = 'Actualités'
        ordering = ['-is_pinned', '-publication_date', '-created_at']

    def __str__(self):
        return f"{self.get_news_type_display()} - {self.title}"

    def get_absolute_url(self):
        return reverse('news:detail', kwargs={'pk': self.pk})
