from django import forms
from django.forms import ModelForm, formset_factory
from .models import Beneficiary, FinancialSnapshot, Child, Interaction


class BeneficiaryForm(ModelForm):
    """Formulaire pour créer/modifier un bénéficiaire"""
    
    class Meta:
        model = Beneficiary
        fields = [
            'civility', 'first_name', 'last_name', 'birth_date', 'phone', 'email',
            'occupation', 'address', 'residence_address', 'housing_status',
            'family_status', 'dependents_count'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'civility': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Prénom'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Nom'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Téléphone'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Email'
            }),
            'occupation': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Métier / Savoir-faire'
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 4,
                'placeholder': 'Adresse de domiciliation'
            }),
            'residence_address': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 4,
                'placeholder': 'Lieu de résidence'
            }),
            'housing_status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'family_status': forms.RadioSelect(attrs={
                'class': 'space-y-2'
            }),
            'dependents_count': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'min': '0'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre SEULEMENT nom et prénom obligatoires
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        
        # Tous les autres champs sont optionnels
        for field_name, field in self.fields.items():
            if field_name not in ['first_name', 'last_name']:
                field.required = False


class FinancialSnapshotForm(ModelForm):
    """Formulaire pour créer un snapshot financier"""
    
    class Meta:
        model = FinancialSnapshot
        exclude = ['beneficiary', 'date']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Rendre TOUS les champs optionnels
        for field_name, field in self.fields.items():
            field.required = False
        
        # Organiser les champs par catégories pour l'affichage
        self.revenue_fields = {
            'Prestations sociales/minimas sociaux': [
                'rsa_prime_activite', 'aah_pension_invalidite', 'apl', 'paje',
                'af', 'cf', 'asf', 'ape_conge_parental'
            ],
            'Revenus': [
                'ij_cpam_msa', 'france_travail', 'retraite_aspa', 'salaire',
                'ada', 'stage_formation_bourses', 'autres_revenus'
            ],
            'Autres revenus': [
                'aide_conseil_departemental', 'pension_alimentaire', 'travail_non_declare',
                'soutien_familial_amical', 'contrat_garantie_jeunes', 'contrat_apprentissage',
                'tickets_service', 'bons_alimentation'
            ]
        }
        
        self.charge_fields = {
            'Logement': [
                'loyer_residuel', 'energie', 'eau', 'assurance_habitation'
            ],
            'Santé et Education': [
                'mutuelle_privee', 'css', 'frais_scolaires', 'frais_sante_non_rembourses'
            ],
            'Transport': [
                'transport_commun', 'carburant'
            ],
            'Engagements financiers': [
                'credit_consommation', 'dettes_diverses', 'abonnements_sport_culture'
            ]
        }
        
        # Appliquer les classes CSS à tous les champs
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'min': '0'
            })
            
            # Pour les champs décimaux, ne pas afficher 0 si la valeur est null
            if hasattr(field, 'initial') and field.initial == 0:
                field.initial = None
                field.widget.attrs['placeholder'] = 'Non renseigné'
    
    def get_revenue_categories(self):
        """Retourne les champs de revenus organisés par catégorie"""
        categories = []
        for category_name, field_names in self.revenue_fields.items():
            fields = [(name, self[name]) for name in field_names if name in self.fields]
            if fields:
                categories.append((category_name, fields))
        return categories
    
    def get_charge_categories(self):
        """Retourne les champs de charges organisés par catégorie"""
        categories = []
        for category_name, field_names in self.charge_fields.items():
            fields = [(name, self[name]) for name in field_names if name in self.fields]
            if fields:
                categories.append((category_name, fields))
        return categories


class ChildForm(ModelForm):
    """Formulaire pour les enfants"""
    
    class Meta:
        model = Child
        fields = ['first_name', 'last_name', 'birth_date', 'observations']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'observations': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            })


# Formset pour gérer plusieurs enfants
ChildFormSet = formset_factory(
    ChildForm,
    extra=0,
    can_delete=True,
    min_num=0,
    max_num=10
)


class InteractionForm(ModelForm):
    """Formulaire pour créer/modifier une interaction"""
    
    class Meta:
        model = Interaction
        fields = [
            'interaction_type', 'title', 'description', 'changes_made',
            'follow_up_required', 'follow_up_date', 'follow_up_notes'
        ]
        widgets = {
            'interaction_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Ex: Demande d\'aide alimentaire'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 6,
                'placeholder': 'Décrivez la situation, les besoins exprimés, les observations...'
            }),
            'changes_made': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 5,
                'placeholder': 'Services activés, modifications apportées, actions entreprises...'
            }),
            'follow_up_required': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'follow_up_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'follow_up_notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Notes concernant le suivi à effectuer...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre certains champs obligatoires
        self.fields['interaction_type'].required = True
        self.fields['title'].required = True
        self.fields['description'].required = True
        
        # Appliquer les classes CSS uniformément
        for field_name, field in self.fields.items():
            if field_name == 'follow_up_required':
                continue  # Le checkbox a déjà ses classes
            
            if 'class' not in field.widget.attrs:
                if isinstance(field.widget, forms.Textarea):
                    field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
                elif isinstance(field.widget, forms.Select):
                    field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
                else:
                    field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500' 