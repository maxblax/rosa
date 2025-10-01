from django import forms
from django.forms import ModelForm
from .models import Partner


class PartnerForm(ModelForm):
    """Formulaire pour créer/modifier un partenaire"""

    # Champ additionnel pour gérer les services individuellement
    new_service = forms.CharField(
        label='Ajouter un service',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Ajouter un service...'
        })
    )

    class Meta:
        model = Partner
        fields = ['name', 'address', 'phone', 'email', 'services']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Nom du partenaire'
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 4,
                'placeholder': 'Adresse complète'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Téléphone'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Email'
            }),
            'services': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Seul le nom est obligatoire
        self.fields['name'].required = True

        # Tous les autres champs sont optionnels
        for field_name, field in self.fields.items():
            if field_name not in ['name']:
                field.required = False
