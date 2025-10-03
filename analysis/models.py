from django.db import models


class ChartConfig(models.Model):
    """Configuration flexible pour les graphiques d'analyse"""

    CHART_TYPE_CHOICES = [
        ('line', 'Graphique en ligne'),
        ('bar', 'Graphique en barres'),
        ('stacked_bar', 'Graphique en barres empilées'),
        ('pie', 'Graphique circulaire'),
        ('doughnut', 'Graphique en anneau'),
        ('heatmap', 'Heatmap'),
    ]

    SIZE_CHOICES = [
        ('half', 'Demi-largeur'),
        ('full', 'Pleine largeur'),
    ]

    SECTION_CHOICES = [
        ('IMPACT', 'Impact Social'),
        ('DEMOGRAPHIC', 'Démographie & Profils'),
        ('FINANCIAL', 'Données Financières'),
        ('OPERATIONAL', 'Opérationnel'),
        ('TRENDS', 'Tendances'),
        ('ADVANCED', 'Visualisations Avancées'),
    ]

    # Configuration de base
    title = models.CharField('Titre', max_length=200)
    description = models.TextField('Description', blank=True, help_text='Description affichée sous le graphique')
    section = models.CharField(
        'Section',
        max_length=20,
        choices=SECTION_CHOICES,
        default='OPERATIONAL',
        help_text='Catégorie de classement du graphique'
    )

    chart_type = models.CharField(
        'Type de graphique',
        max_length=20,
        choices=CHART_TYPE_CHOICES,
        default='bar'
    )

    # Position et taille
    display_order = models.IntegerField('Ordre d\'affichage', default=0, help_text='Plus petit = affiché en premier')
    size = models.CharField(
        'Taille',
        max_length=10,
        choices=SIZE_CHOICES,
        default='full'
    )

    # Requête Django (sera évaluée de manière sécurisée)
    query_code = models.TextField(
        'Code de requête',
        help_text='Code Python pour générer les données. Doit retourner un dict avec "labels" et "datasets".'
    )

    # Configuration visuelle
    y_axis_label = models.CharField('Label axe Y', max_length=100, blank=True)
    x_axis_label = models.CharField('Label axe X', max_length=100, blank=True)

    # Activation
    is_active = models.BooleanField('Actif', default=True)

    # Métadonnées
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)

    class Meta:
        verbose_name = 'Configuration de graphique'
        verbose_name_plural = 'Configurations de graphiques'
        ordering = ['display_order', 'title']

    def __str__(self):
        return f"{self.title} ({self.get_chart_type_display()})"

    def get_chart_data(self):
        """
        Exécute le code de requête et retourne les données du graphique.
        IMPORTANT: À sécuriser en production (sandboxing)
        """
        try:
            # Imports disponibles dans le contexte d'exécution
            from django.db.models import Count, Sum, Avg, Q
            from django.utils import timezone
            from datetime import datetime, timedelta
            from beneficiaries.models import Beneficiary, Interaction, FinancialSnapshot, Child
            from calendar_app.models import Appointment
            from volunteers.models import Volunteer
            from stock.models import Product

            # Contexte d'exécution sécurisé
            local_context = {
                'Count': Count,
                'Sum': Sum,
                'Avg': Avg,
                'Q': Q,
                'timezone': timezone,
                'datetime': datetime,
                'timedelta': timedelta,
                'Beneficiary': Beneficiary,
                'Interaction': Interaction,
                'FinancialSnapshot': FinancialSnapshot,
                'Child': Child,
                'Appointment': Appointment,
                'Volunteer': Volunteer,
                'Product': Product,
            }

            # Exécution du code
            exec(self.query_code, local_context)

            # Le code doit définir une variable 'result'
            return local_context.get('result', {'labels': [], 'datasets': []})

        except Exception as e:
            # En cas d'erreur, retourner un message d'erreur
            return {
                'error': str(e),
                'labels': [],
                'datasets': []
            }
