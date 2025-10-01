from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from .models import Volunteer


class VolunteerForm(ModelForm):
    """Formulaire pour créer/modifier un bénévole"""

    # Champs pour créer l'utilisateur Django
    username = forms.CharField(
        label='Nom d\'utilisateur',
        max_length=150,
        help_text='Nom d\'utilisateur pour se connecter à l\'application'
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(),
        required=False,
        help_text='Laissez vide pour ne pas modifier le mot de passe'
    )
    password_confirm = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(),
        required=False
    )

    class Meta:
        model = Volunteer
        fields = [
            'civility', 'role', 'status', 'birth_date', 'phone', 'address',
            'skills', 'join_date'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'join_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'civility': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'role': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Téléphone'
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 4,
                'placeholder': 'Adresse complète'
            }),
            'skills': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 4,
                'placeholder': 'Compétences particulières, expériences...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.is_edit = kwargs.pop('is_edit', False)
        super().__init__(*args, **kwargs)

        # Champs User
        self.fields['first_name'] = forms.CharField(
            label='Prénom',
            max_length=30,
            widget=forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Prénom'
            })
        )
        self.fields['last_name'] = forms.CharField(
            label='Nom',
            max_length=150,
            widget=forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Nom'
            })
        )
        self.fields['email'] = forms.EmailField(
            label='Email',
            required=False,
            widget=forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Email'
            })
        )

        # Ajouter les classes CSS aux autres champs
        for field_name, field in self.fields.items():
            if field_name not in ['username', 'password', 'password_confirm', 'first_name', 'last_name', 'email']:
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'

        # Ajouter les classes aux champs username et password
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Nom d\'utilisateur'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
        self.fields['password_confirm'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })

        # Rendre certains champs obligatoires
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['username'].required = True
        self.fields['role'].required = True

        # Si c'est une édition, préremplir les champs User
        if self.is_edit and self.instance.pk and hasattr(self.instance, 'user'):
            user = self.instance.user
            self.fields['username'].initial = user.username
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

            # Ne pas exiger de mot de passe en mode édition
            self.fields['password'].required = False
            self.fields['password_confirm'].required = False
        else:
            # En mode création, mot de passe obligatoire
            self.fields['password'].required = True
            self.fields['password_confirm'].required = True

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        username = cleaned_data.get('username')

        # Vérification du mot de passe
        if password or password_confirm:
            if password != password_confirm:
                raise forms.ValidationError("Les mots de passe ne correspondent pas.")

        # Vérification de l'unicité du nom d'utilisateur
        if username:
            if self.is_edit and self.instance.pk:
                # En mode édition, vérifier que le username n'est pas pris par un autre utilisateur
                if User.objects.filter(username=username).exclude(pk=self.instance.user.pk).exists():
                    raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
            else:
                # En mode création, vérifier que le username n'existe pas
                if User.objects.filter(username=username).exists():
                    raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé.")

        return cleaned_data