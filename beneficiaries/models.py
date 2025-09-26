from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class Beneficiary(models.Model):
    """Modèle pour les bénéficiaires de l'association"""
    
    CIVILITY_CHOICES = [
        ('M', 'M.'),
        ('MME', 'Mme'),
        ('AUTRE', 'Autre'),
    ]
    
    HOUSING_STATUS_CHOICES = [
        ('CADA', 'CADA'),
        ('CAO', 'CAO'),
        ('CHRS', 'CHRS'),
        ('DIFFUS', 'Logement Diffus'),
        ('COLLECTIF', 'Collectif'),
        ('QPV', 'Quartier QPV'),
        ('AUTRE', 'Autre'),
    ]
    
    FAMILY_STATUS_CHOICES = [
        ('CELIBATAIRE', 'Célibataire'),
        ('MARIE', 'Marié(e)'),
        ('VEUF', 'Veuf/Veuve'),
        ('VIE_MARITALE', 'Vie maritale'),
        ('DIVORCE', 'Divorcé(e)'),
        ('SEPARE', 'Séparé(e)'),
    ]
    
    # Informations personnelles
    civility = models.CharField('Civilité', max_length=10, choices=CIVILITY_CHOICES, blank=True)
    first_name = models.CharField('Prénom', max_length=100)
    last_name = models.CharField('Nom', max_length=100)
    birth_date = models.DateField('Date de naissance', null=True, blank=True)
    phone = models.CharField('Téléphone', max_length=20, blank=True)
    email = models.EmailField('Email', blank=True)
    
    # Adresses
    address = models.TextField('Adresse de domiciliation', blank=True)
    residence_address = models.TextField('Lieu de résidence', blank=True)
    
    # Situation
    occupation = models.CharField('Métier / Savoir-faire', max_length=200, blank=True)
    housing_status = models.CharField(
        'Hébergement', 
        max_length=20, 
        choices=HOUSING_STATUS_CHOICES,
        blank=True
    )
    family_status = models.CharField(
        'Situation Familiale',
        max_length=20,
        choices=FAMILY_STATUS_CHOICES,
        default='CELIBATAIRE'
    )
    dependents_count = models.PositiveIntegerField('Nombre d\'enfants à charge', default=0)
    
    # Métadonnées
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)
    
    class Meta:
        verbose_name = 'Bénéficiaire'
        verbose_name_plural = 'Bénéficiaires'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.get_civility_display()} {self.first_name} {self.last_name}"
    
    def get_absolute_url(self):
        return reverse('beneficiaries:detail', kwargs={'pk': self.pk})
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def latest_financial_snapshot(self):
        """Retourne la dernière photo instantanée financière"""
        return self.financial_snapshots.order_by('-date').first()


class FinancialSnapshot(models.Model):
    """Photo instantanée financière d'un bénéficiaire à un moment donné"""
    
    beneficiary = models.ForeignKey(
        Beneficiary, 
        on_delete=models.CASCADE,
        related_name='financial_snapshots',
        verbose_name='Bénéficiaire'
    )
    date = models.DateTimeField('Date de la photo instantanée', auto_now_add=True)
    
    # Revenus - Prestations sociales/minimas sociaux
    rsa_prime_activite = models.DecimalField(
        'RSA/Prime d\'activité', 
        max_digits=10, 
        decimal_places=2, 
        null=True,
        blank=True
    )
    aah_pension_invalidite = models.DecimalField(
        'AAH, PI (pension d\'invalidité)',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    apl = models.DecimalField(
        'APL (Bailleur ou bénéficiaire)',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    paje = models.DecimalField('PAJE', max_digits=10, decimal_places=2, default=0)
    af = models.DecimalField(
        'AF (Allocations Familiales)',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    cf = models.DecimalField(
        'CF (Complément Familial)',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    asf = models.DecimalField(
        'ASF (Allocation de Soutien Familial)',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    ape_conge_parental = models.DecimalField(
        'APE Congé Parental',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Revenus
    ij_cpam_msa = models.DecimalField(
        'IJ CPAM/MSA',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    france_travail = models.DecimalField(
        'France Travail',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    retraite_aspa = models.DecimalField(
        'Retraite, A.S.P.A.',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    salaire = models.DecimalField('Salaire', max_digits=10, decimal_places=2, default=0)
    ada = models.DecimalField(
        'Allocation Demandeur d\'Asile (ADA)',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    stage_formation_bourses = models.DecimalField(
        'Stage, Formation, bourses',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    autres_revenus = models.DecimalField(
        'Autres revenus',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Autres revenus
    aide_conseil_departemental = models.DecimalField(
        'Aide Conseil Départemental',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    pension_alimentaire = models.DecimalField(
        'Pension alimentaire',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    travail_non_declare = models.DecimalField(
        'Travail non déclaré',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    soutien_familial_amical = models.DecimalField(
        'Soutien familial ou amical',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    contrat_garantie_jeunes = models.DecimalField(
        'Contrat Garantie Jeunes (MLJ)',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    contrat_apprentissage = models.DecimalField(
        'Contrat d\'apprentissage',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    tickets_service = models.DecimalField(
        'Tickets service',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    bons_alimentation = models.DecimalField(
        'Bons d\'alimentation',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Charges - Logement
    loyer_residuel = models.DecimalField(
        'Loyer résiduel',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    energie = models.DecimalField('Énergie', max_digits=10, decimal_places=2, default=0)
    eau = models.DecimalField('Eau', max_digits=10, decimal_places=2, default=0)
    assurance_habitation = models.DecimalField(
        'Assurance habitation',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Charges - Santé et Education
    mutuelle_privee = models.DecimalField(
        'Mutuelle privée',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    css = models.DecimalField(
        'CSS (Complémentaire Santé Solidaire)',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    frais_scolaires = models.DecimalField(
        'Frais scolaires (cantine, sorties)',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    frais_sante_non_rembourses = models.DecimalField(
        'Frais de santé non remboursés',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Charges - Transport
    transport_commun = models.DecimalField(
        'Transport en commun',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    carburant = models.DecimalField('Carburant', max_digits=10, decimal_places=2, default=0)
    
    # Charges - Engagements financiers
    credit_consommation = models.DecimalField(
        'Crédit à la consommation',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    dettes_diverses = models.DecimalField(
        'Dettes diverses',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    abonnements_sport_culture = models.DecimalField(
        'Abonnements sport et culture',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    class Meta:
        verbose_name = 'Photo Instantanée Financière'
        verbose_name_plural = 'Photos Instantanées Financières'
        ordering = ['-date']
    
    def __str__(self):
        return f"Photo instantanée {self.beneficiary} - {self.date.strftime('%d/%m/%Y')}"
    
    @property
    def total_revenus(self):
        """Calcule le total des revenus"""
        revenus = [
            self.rsa_prime_activite or 0, self.aah_pension_invalidite or 0, self.apl or 0, self.paje or 0,
            self.af or 0, self.cf or 0, self.asf or 0, self.ape_conge_parental or 0, self.ij_cpam_msa or 0,
            self.france_travail or 0, self.retraite_aspa or 0, self.salaire or 0, self.ada or 0,
            self.stage_formation_bourses or 0, self.autres_revenus or 0, self.aide_conseil_departemental or 0,
            self.pension_alimentaire or 0, self.travail_non_declare or 0, self.soutien_familial_amical or 0,
            self.contrat_garantie_jeunes or 0, self.contrat_apprentissage or 0, self.tickets_service or 0,
            self.bons_alimentation or 0
        ]
        return sum(revenus)
    
    @property
    def total_charges(self):
        """Calcule le total des charges"""
        charges = [
            self.loyer_residuel or 0, self.energie or 0, self.eau or 0, self.assurance_habitation or 0,
            self.mutuelle_privee or 0, self.css or 0, self.frais_scolaires or 0, self.frais_sante_non_rembourses or 0,
            self.transport_commun or 0, self.carburant or 0, self.credit_consommation or 0, self.dettes_diverses or 0,
            self.abonnements_sport_culture or 0
        ]
        return sum(charges)
    
    @property
    def solde_net(self):
        """Calcule le solde net (revenus - charges)"""
        return self.total_revenus - self.total_charges


class Child(models.Model):
    """Modèle pour représenter les enfants d'un bénéficiaire"""
    beneficiary = models.ForeignKey(
        Beneficiary, 
        on_delete=models.CASCADE, 
        related_name='children', 
        verbose_name='Bénéficiaire'
    )
    first_name = models.CharField('Prénom', max_length=100)
    last_name = models.CharField('Nom', max_length=100)
    birth_date = models.DateField('Date de naissance')
    observations = models.TextField('Observations', blank=True, help_text='Notes sur l\'enfant')
    
    # Timestamps
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)

    class Meta:
        verbose_name = 'Enfant'
        verbose_name_plural = 'Enfants'
        ordering = ['birth_date']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        """Calcule l'âge de l'enfant"""
        from datetime import date
        today = date.today()
        age = today.year - self.birth_date.year
        if today.month < self.birth_date.month or (today.month == self.birth_date.month and today.day < self.birth_date.day):
            age -= 1
        return age

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Interaction(models.Model):
    """Modèle pour enregistrer les interactions avec les bénéficiaires"""
    
    INTERACTION_TYPE_CHOICES = [
        ('ASSOCIATION', 'Entretien à l\'association'),
        ('EXTERNAL', 'Entretien externe'),
        ('PHONE', 'Entretien téléphonique'),
        ('HOME_VISIT', 'Visite à domicile'),
        ('EMAIL', 'Contact par email'),
        ('OTHER', 'Autre'),
    ]
    
    # Relations
    beneficiary = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name='interactions',
        verbose_name='Bénéficiaire'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='beneficiary_interactions',
        verbose_name='Utilisateur',
        null=True,
        blank=True
    )
    
    # Détails de l'interaction
    interaction_type = models.CharField(
        'Type d\'interaction',
        max_length=20,
        choices=INTERACTION_TYPE_CHOICES,
        default='ASSOCIATION'
    )
    title = models.CharField('Titre', max_length=200)
    description = models.TextField('Description', blank=True)
    
    # Suivi financier (optionnel)
    financial_snapshot = models.ForeignKey(
        FinancialSnapshot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interaction',
        verbose_name='Photo instantanée financière associée'
    )
    
    # Actions/changements apportés
    changes_made = models.TextField(
        'Changements apportés',
        blank=True,
        help_text='Décrivez les actions, services activés, modifications apportées'
    )
    
    # Suivi
    follow_up_required = models.BooleanField(
        'Suivi requis',
        default=False,
        help_text='Cette interaction nécessite-t-elle un suivi ?'
    )
    follow_up_date = models.DateField(
        'Date de suivi',
        null=True,
        blank=True,
        help_text='Date prévue pour le suivi'
    )
    follow_up_notes = models.TextField(
        'Notes de suivi',
        blank=True,
        help_text='Notes concernant le suivi à effectuer'
    )
    
    # Métadonnées
    created_at = models.DateTimeField('Date de l\'interaction', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)
    
    class Meta:
        verbose_name = 'Interaction'
        verbose_name_plural = 'Interactions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.beneficiary.full_name} ({self.created_at.strftime('%d/%m/%Y')})"
    
    def get_absolute_url(self):
        return reverse('beneficiaries:interaction_detail', kwargs={
            'beneficiary_pk': self.beneficiary.pk,
            'pk': self.pk
        })
    
    @property
    def interaction_type_icon(self):
        """Retourne l'icône FontAwesome appropriée selon le type d'interaction"""
        icons = {
            'ASSOCIATION': 'fas fa-user',
            'EXTERNAL': 'fas fa-calendar',
            'PHONE': 'fas fa-phone',
            'HOME_VISIT': 'fas fa-home',
            'EMAIL': 'fas fa-envelope',
            'OTHER': 'fas fa-comment',
        }
        return icons.get(self.interaction_type, 'fas fa-comment')
    
    @property
    def short_description(self):
        """Retourne une version tronquée de la description"""
        if len(self.description) <= 100:
            return self.description
        return self.description[:97] + '...'