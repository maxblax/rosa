from django.contrib import admin
from .models import Beneficiary, FinancialSnapshot, Child, Interaction


@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'civility', 'birth_date', 'phone', 'email', 'family_status', 'created_at']
    list_filter = ['civility', 'family_status', 'housing_status', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    ordering = ['last_name', 'first_name']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('civility', 'first_name', 'last_name', 'birth_date', 'phone', 'email')
        }),
        ('Adresses', {
            'fields': ('address', 'residence_address')
        }),
        ('Situation', {
            'fields': ('occupation', 'housing_status', 'family_status', 'dependents_count')
        }),
    )


@admin.register(FinancialSnapshot)
class FinancialSnapshotAdmin(admin.ModelAdmin):
    list_display = ['beneficiary', 'date', 'total_revenus', 'total_charges', 'solde_net']
    list_filter = ['date', 'beneficiary__family_status']
    search_fields = ['beneficiary__first_name', 'beneficiary__last_name']
    ordering = ['-date']
    readonly_fields = ['date']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('beneficiary', 'date')
        }),
        ('Prestations sociales/minimas sociaux', {
            'fields': ('rsa_prime_activite', 'aah_pension_invalidite', 'apl', 'paje', 'af', 'cf', 'asf', 'ape_conge_parental'),
            'classes': ['collapse']
        }),
        ('Revenus', {
            'fields': ('ij_cpam_msa', 'france_travail', 'retraite_aspa', 'salaire', 'ada', 'stage_formation_bourses', 'autres_revenus'),
            'classes': ['collapse']
        }),
        ('Autres revenus', {
            'fields': ('aide_conseil_departemental', 'pension_alimentaire', 'travail_non_declare', 'soutien_familial_amical', 'contrat_garantie_jeunes', 'contrat_apprentissage', 'tickets_service', 'bons_alimentation'),
            'classes': ['collapse']
        }),
        ('Charges - Logement', {
            'fields': ('loyer_residuel', 'energie', 'eau', 'assurance_habitation'),
            'classes': ['collapse']
        }),
        ('Charges - Santé et Education', {
            'fields': ('mutuelle_privee', 'css', 'frais_scolaires', 'frais_sante_non_rembourses'),
            'classes': ['collapse']
        }),
        ('Charges - Transport', {
            'fields': ('transport_commun', 'carburant'),
            'classes': ['collapse']
        }),
        ('Charges - Engagements financiers', {
            'fields': ('credit_consommation', 'dettes_diverses', 'abonnements_sport_culture'),
            'classes': ['collapse']
        }),
    )


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'age', 'beneficiary', 'birth_date']
    list_filter = ['birth_date', 'beneficiary']
    search_fields = ['first_name', 'last_name', 'beneficiary__first_name', 'beneficiary__last_name']
    ordering = ['beneficiary', 'birth_date']


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('title', 'beneficiary', 'interaction_type', 'user', 'created_at', 'follow_up_required')
    list_filter = ('interaction_type', 'follow_up_required', 'created_at', 'user')
    search_fields = ('title', 'description', 'beneficiary__first_name', 'beneficiary__last_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('beneficiary', 'user', 'interaction_type', 'title', 'description')
        }),
        ('Actions et changements', {
            'fields': ('changes_made', 'financial_snapshot')
        }),
        ('Suivi', {
            'fields': ('follow_up_required', 'follow_up_date', 'follow_up_notes')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
