# -*- coding: utf-8 -*-
from django import forms
from datetime import date

from rosa.form_fields import TolerantDateField, TolerantDecimalField
from .models import Donation


class donationForm(forms.ModelForm):
    """Formulaire pour creer/modifier un don manuel"""

    date = TolerantDateField(required=False, label='Date du don', widget=forms.TextInput(attrs={
        'inputmode': 'numeric', 'placeholder': 'JJ/MM/AAAA', 'autocomplete': 'off', 'data-tolerant-date': 'true',
        'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
    }))

    amount = TolerantDecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        label='Montant',
        help_text='Montant du don en euros',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'inputmode': 'decimal',
            'placeholder': 'Montant en euros (ex : 1 200,50)',
        }),
    )

    class Meta:
        model = Donation
        fields = ['donor_name', 'amount', 'payment_type', 'date', 'is_anonymous', 'notes']
        widgets = {
            'donor_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Nom du drosateur (laisser vide pour anonyme)'
            }),
            'payment_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'is_anonymous': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:ring-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 4,
                'placeholder': 'Notes ou commentaires'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default date to today for new donations
        if not self.instance.pk and 'date' not in self.initial:
            self.initial['date'] = date.today()
