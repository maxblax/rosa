from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Donation(models.Model):
    """
    Modèle pour les dons manuels enregistrés dans l'application.
    Les dons HelloAsso ne sont PAS stockés en base de données.
    """

    PAYMENT_TYPE_CHOICES = [
        ('CASH', 'Espèces'),
        ('TRANSFER', 'Virement bancaire'),
        ('CARD', 'Paiement par carte'),
        ('CHECK', 'Chèque'),
    ]

    donor_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nom du donateur",
        help_text="Laisser vide pour un don anonyme"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Montant",
        help_text="Montant du don en euros"
    )

    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        verbose_name="Type de paiement"
    )

    date = models.DateField(
        default=timezone.now,
        verbose_name="Date du don"
    )

    is_anonymous = models.BooleanField(
        default=False,
        verbose_name="Don anonyme"
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes",
        help_text="Notes ou commentaires sur ce don"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='donations_created',
        verbose_name="Créé par"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )

    class Meta:
        verbose_name = "Don manuel"
        verbose_name_plural = "Dons manuels"
        ordering = ['-date', '-created_at']

    def __str__(self):
        donor = self.donor_name if self.donor_name and not self.is_anonymous else "Anonyme"
        return f"{donor} - {self.amount}€ ({self.get_payment_type_display()}) - {self.date}"

    @property
    def source(self):
        """Toujours 'Manuel' pour les dons enregistrés en base de données"""
        return "Manuel"
