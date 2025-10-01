from django.db import models


class Product(models.Model):
    """Product model for stock management."""

    CATEGORY_CHOICES = [
        ('ALIMENTAIRE', 'Alimentaire'),
        ('HYGIENE', 'Hygiene'),
        ('VETEMENT', 'Vetement'),
        ('MOBILIER', 'Mobilier'),
        ('SCOLAIRE', 'Scolaire'),
        ('AUTRE', 'Autre'),
    ]

    name = models.CharField(
        max_length=200,
        verbose_name='Nom du produit',
        help_text='Nom ou description du produit'
    )

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='AUTRE',
        verbose_name='Categorie'
    )

    quantity = models.IntegerField(
        default=0,
        verbose_name='Quantite en stock',
        help_text='Quantite actuelle disponible'
    )

    unit = models.CharField(
        max_length=50,
        default='unite',
        verbose_name='Unite de mesure',
        help_text='Ex: unite, kg, litre, boite, etc.'
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Description',
        help_text='Details supplementaires sur le produit'
    )

    min_threshold = models.IntegerField(
        default=0,
        verbose_name='Seuil minimum',
        help_text='Alerte si la quantite descend en dessous de cette valeur'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date de creation')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Derniere modification')

    class Meta:
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"

    @property
    def is_low_stock(self):
        """Returns True if stock is below minimum threshold."""
        return self.quantity <= self.min_threshold
