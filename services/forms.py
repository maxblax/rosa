from django import forms

from rosa.form_fields import TolerantDecimalField, TolerantDateField
from .models import Service, ServiceSession, FinancialAidRequest
from . import logic

INPUT_CLASSES = ('w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none '
                 'focus:ring-2 focus:ring-blue-500 focus:border-blue-500')
CHECKBOX_CLASSES = 'h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'


class InteractionServicesForm(forms.Form):
    """Services attribués pendant un entretien (bloc ajouté au formulaire d'entretien).

    Les champs sont générés à partir du catalogue actif :
    - svc_<id> : case d'inscription / d'orientation ;
    - svc_<id>_session : date choisie (distributions à date choisie) ;
    - svc_<id>_details : précision en toutes lettres (services simples) ;
    - aid_* : demande d'aide financière.
    """
    prefix = 'svc'

    aid_requested = forms.BooleanField(required=False, label="Demander une aide financière",
                                       widget=forms.CheckboxInput(attrs={'class': CHECKBOX_CLASSES}))
    aid_amount = TolerantDecimalField(
        required=False, max_digits=10, decimal_places=2, min_value=0, label='Montant (€)',
        widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'inputmode': 'decimal',
                                      'placeholder': 'ex : 50 ou 1 200,50'}))
    aid_nature = forms.ChoiceField(required=False, label='Nature', choices=FinancialAidRequest.NATURE_CHOICES,
                                   initial='AUTRE', widget=forms.Select(attrs={'class': INPUT_CLASSES}))
    aid_reason = forms.CharField(required=False, label='Motif (en toutes lettres)',
                                 widget=forms.Textarea(attrs={'class': INPUT_CLASSES, 'rows': 3,
                                                              'placeholder': 'Carte de bus, cantine du mois de mars...'}))

    def __init__(self, *args, beneficiary=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.beneficiary = beneficiary
        self.services = list(Service.objects.filter(is_active=True).select_related('partner'))
        self.financial_service = next((s for s in self.services if s.is_financial), None)
        self.composition = logic.household_composition(beneficiary) if beneficiary else None
        self.session_choices = {}

        for service in self.services:
            if service.is_financial:
                continue
            self.fields[f'{service.pk}'] = forms.BooleanField(
                required=False, label=service.name,
                widget=forms.CheckboxInput(attrs={'class': CHECKBOX_CLASSES, 'data-service-toggle': service.pk}))
            if service.is_distribution and not service.is_auto_scheduled:
                sessions = logic.sessions_preview(service)
                self.session_choices[service.pk] = sessions
                self.fields[f'{service.pk}_session'] = forms.ModelChoiceField(
                    required=False, queryset=ServiceSession.objects.filter(pk__in=[s.pk for s in sessions]),
                    widget=forms.RadioSelect)
            if service.is_simple:
                self.fields[f'{service.pk}_details'] = forms.CharField(
                    required=False, label='Précision',
                    widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Précision (facultatif)'
                                                  if not service.requires_details else 'À préciser'}))
                if service.category == Service.CATEGORY_EXTERNAL:
                    self.fields[f'{service.pk}_partner'] = forms.CharField(
                        required=False, label='Partenaire',
                        widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'list': 'partners-datalist',
                                                      'placeholder': 'Nom du partenaire'}))

    # Accès pour le template
    def groups(self):
        """Services regroupés par catégorie avec leurs champs liés."""
        grouped = []
        for category, label in Service.CATEGORY_CHOICES:
            items = []
            for service in self.services:
                if service.is_financial or service.category != category:
                    continue
                items.append({
                    'service': service,
                    'field': self[f'{service.pk}'],
                    'sessions': [
                        {'session': s, 'checked': str(self[f'{service.pk}_session'].value()) == str(s.pk),
                         'available': s.can_accept(self._first_part_persons(service))}
                        for s in self.session_choices.get(service.pk, [])
                    ],
                    'details': self[f'{service.pk}_details'] if f'{service.pk}_details' in self.fields else None,
                    'partner': self[f'{service.pk}_partner'] if f'{service.pk}_partner' in self.fields else None,
                    'session_field_name': self.add_prefix(f'{service.pk}_session'),
                })
            if items:
                grouped.append({'label': label, 'items': items})
        return grouped

    def _first_part_persons(self, service):
        if not self.composition:
            return 1
        return logic.split_composition(service, self.composition)[0].persons

    def clean(self):
        cleaned = super().clean()
        for service in self.services:
            if service.is_financial or not cleaned.get(f'{service.pk}'):
                continue
            if service.is_distribution:
                if self.beneficiary and logic.has_pending_bookings(self.beneficiary, service):
                    self.add_error(f'{service.pk}',
                                   f"La famille a déjà une inscription en cours pour {service.name}.")
                if not service.is_auto_scheduled and not cleaned.get(f'{service.pk}_session'):
                    self.add_error(f'{service.pk}', f"Choisissez une date pour {service.name}.")
            if service.is_simple and service.requires_details and not cleaned.get(f'{service.pk}_details', '').strip():
                self.add_error(f'{service.pk}_details', f"Précisez en toutes lettres pour « {service.name} ».")

        if cleaned.get('aid_requested'):
            if not cleaned.get('aid_amount'):
                self.add_error('aid_amount', 'Indiquez le montant demandé.')
            if not (cleaned.get('aid_reason') or '').strip():
                self.add_error('aid_reason', 'Indiquez le motif de la demande.')
        return cleaned

    def has_selection(self):
        return bool(self.cleaned_data.get('aid_requested')) or any(
            self.cleaned_data.get(f'{s.pk}') for s in self.services if not s.is_financial)

    def save(self, interaction, user):
        """Crée les inscriptions et la demande d'aide. Renvoie (inscriptions, demande)."""
        from .notifications import notify_new_request

        registrations = []
        for service in self.services:
            if service.is_financial or not self.cleaned_data.get(f'{service.pk}'):
                continue
            if service.is_distribution:
                registrations.append(logic.register_distribution(
                    self.beneficiary, service, user=user, interaction=interaction,
                    first_session=self.cleaned_data.get(f'{service.pk}_session')))
            else:
                registrations.append(logic.register_simple(
                    self.beneficiary, service, user=user, interaction=interaction,
                    details=self.cleaned_data.get(f'{service.pk}_details', ''),
                    partner_name=self.cleaned_data.get(f'{service.pk}_partner', '')))

        aid = None
        if self.cleaned_data.get('aid_requested'):
            aid = FinancialAidRequest.objects.create(
                beneficiary=self.beneficiary, interaction=interaction,
                amount=self.cleaned_data['aid_amount'], nature=self.cleaned_data.get('aid_nature') or 'AUTRE',
                reason=self.cleaned_data['aid_reason'].strip(), requested_by=user,
            )
            notify_new_request(aid)
        return registrations, aid


class AidDecisionForm(forms.Form):
    decision = forms.ChoiceField(choices=[('APPROVED', 'Valider'), ('REJECTED', 'Refuser')], widget=forms.RadioSelect)
    rejection_reason = forms.CharField(required=False, label='Motif du refus',
                                       widget=forms.Textarea(attrs={'class': INPUT_CLASSES, 'rows': 3}))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('decision') == 'REJECTED' and not (cleaned.get('rejection_reason') or '').strip():
            self.add_error('rejection_reason', 'Une explication est obligatoire en cas de refus.')
        return cleaned


class AidPaymentForm(forms.ModelForm):
    paid_at = TolerantDateField(label='Versée le')

    class Meta:
        model = FinancialAidRequest
        fields = ['paid_at', 'payment_method', 'payment_notes']
        widgets = {
            'payment_method': forms.Select(attrs={'class': INPUT_CLASSES}),
            'payment_notes': forms.Textarea(attrs={'class': INPUT_CLASSES, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].required = True
        self.fields['paid_at'].widget.attrs['class'] = INPUT_CLASSES


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            'name', 'description', 'kind', 'category', 'partner', 'requires_details', 'is_active', 'order',
            'session_weekday', 'session_start', 'session_end', 'sessions_per_registration', 'scheduling',
            'session_capacity', 'capacity_unit', 'max_adults_per_booking', 'max_children_per_booking',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'session_start': forms.TimeInput(attrs={'type': 'time'}),
            'session_end': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = CHECKBOX_CLASSES
            else:
                field.widget.attrs['class'] = INPUT_CLASSES

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('kind') == Service.KIND_DISTRIBUTION and cleaned.get('session_weekday') is None:
            self.add_error('session_weekday', 'Indiquez le jour des sessions de distribution.')
        return cleaned


class SessionForm(forms.ModelForm):
    class Meta:
        model = ServiceSession
        fields = ['capacity', 'is_closed', 'notes']
        widgets = {
            'capacity': forms.NumberInput(attrs={'class': INPUT_CLASSES, 'min': 0}),
            'is_closed': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASSES}),
            'notes': forms.TextInput(attrs={'class': INPUT_CLASSES}),
        }


class AddFamilyToSessionForm(forms.Form):
    beneficiary = forms.ModelChoiceField(queryset=None, label='Famille',
                                         widget=forms.Select(attrs={'class': INPUT_CLASSES}))

    def __init__(self, *args, **kwargs):
        from beneficiaries.models import Beneficiary
        super().__init__(*args, **kwargs)
        self.fields['beneficiary'].queryset = Beneficiary.objects.order_by('last_name', 'first_name')
