from django import forms

from rosa.form_fields import TolerantDecimalField, TolerantDateField
from .models import Service, ServiceScheduleSlot, ServiceSession, FinancialAidRequest
from . import logic

INPUT_CLASSES = ('w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none '
                 'focus:ring-2 focus:ring-blue-500 focus:border-blue-500')
CHECKBOX_CLASSES = 'h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'


class InteractionServicesForm(forms.Form):
    """Services attribués pendant un entretien (bloc ajouté au formulaire d'entretien).

    Les champs sont générés à partir du catalogue actif :
    - svc_<id> : case d'inscription / d'orientation ;
    - svc_<id>_tickets : nombre de passages accordés (distributions) ;
    - svc_<id>_sessions : dates cochées dans la grille des semaines (distributions) ;
    - svc_<id>_details / svc_<id>_partner : précision et partenaire (services simples) ;
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
        self.active_registrations = {}

        for service in self.services:
            if service.is_financial:
                continue
            self.fields[f'{service.pk}'] = forms.BooleanField(
                required=False, label=service.name,
                widget=forms.CheckboxInput(attrs={'class': CHECKBOX_CLASSES}))
            if service.is_distribution:
                sessions = logic.upcoming_sessions(service)
                self.session_choices[service.pk] = sessions
                if beneficiary:
                    self.active_registrations[service.pk] = logic.active_registration(beneficiary, service)
                tickets = logic.default_tickets(service, beneficiary) if beneficiary else service.default_tickets
                self.fields[f'{service.pk}_tickets'] = forms.IntegerField(
                    required=False, min_value=1, max_value=20, initial=tickets, label='Passages accordés',
                    widget=forms.NumberInput(attrs={'class': INPUT_CLASSES + ' w-20', 'min': 1}))
                self.fields[f'{service.pk}_sessions'] = forms.ModelMultipleChoiceField(
                    required=False, queryset=ServiceSession.objects.filter(pk__in=[s.pk for s in sessions]),
                    widget=forms.CheckboxSelectMultiple)
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

    def _selected_session_ids(self, service):
        if self.is_bound:
            return {str(v) for v in self.data.getlist(self.add_prefix(f'{service.pk}_sessions'))}
        return set()

    def _persons(self, service):
        if not self.composition:
            return 1
        return logic.split_composition(service, self.composition)[0].persons

    # Accès pour le template
    def groups(self):
        """Services regroupés par catégorie avec leurs champs liés."""
        grouped = []
        for category, label in Service.CATEGORY_CHOICES:
            items = []
            for service in self.services:
                if service.is_financial or service.category != category:
                    continue
                item = {
                    'service': service,
                    'field': self[f'{service.pk}'],
                    'details': self[f'{service.pk}_details'] if f'{service.pk}_details' in self.fields else None,
                    'partner': self[f'{service.pk}_partner'] if f'{service.pk}_partner' in self.fields else None,
                }
                if service.is_distribution:
                    selected = self._selected_session_ids(service)
                    persons = self._persons(service)
                    item.update({
                        'tickets': self[f'{service.pk}_tickets'],
                        'sessions_field_name': self.add_prefix(f'{service.pk}_sessions'),
                        'sessions_errors': self[f'{service.pk}_sessions'].errors,
                        'active_registration': self.active_registrations.get(service.pk),
                        'weeks': [
                            (monday, [{'session': s, 'checked': str(s.pk) in selected,
                                       'available': s.can_accept(persons)} for s in sessions])
                            for monday, sessions in logic.sessions_by_week(self.session_choices[service.pk])
                        ],
                    })
                items.append(item)
            if items:
                grouped.append({'label': label, 'items': items})
        return grouped

    def clean(self):
        cleaned = super().clean()
        for service in self.services:
            if service.is_financial or not cleaned.get(f'{service.pk}'):
                continue
            if service.is_distribution:
                if self.active_registrations.get(service.pk):
                    self.add_error(f'{service.pk}',
                                   f"La famille a déjà une inscription en cours pour {service.name} : "
                                   f"utilisez ses passages restants depuis sa fiche.")
                    continue
                sessions = list(cleaned.get(f'{service.pk}_sessions') or [])
                tickets = cleaned.get(f'{service.pk}_tickets') or service.default_tickets
                if len(sessions) > tickets:
                    self.add_error(f'{service.pk}_sessions',
                                   f"{len(sessions)} dates cochées pour {tickets} passage(s).")
                if service.max_bookings_per_week:
                    per_week = {}
                    for s in sessions:
                        per_week.setdefault(logic.week_start(s.date), 0)
                        per_week[logic.week_start(s.date)] += 1
                    if any(n > service.max_bookings_per_week for n in per_week.values()):
                        self.add_error(f'{service.pk}_sessions',
                                       f"{service.max_bookings_per_week} passage(s) maximum par semaine.")
                full = [s for s in sessions if not s.can_accept(self._persons(service))]
                if full:
                    self.add_error(f'{service.pk}_sessions',
                                   'Complet ou annulé : ' + ', '.join(f"{s.date:%d/%m}" for s in full))
            if service.is_simple and service.requires_details and not cleaned.get(f'{service.pk}_details', '').strip():
                self.add_error(f'{service.pk}_details', f"Précisez en toutes lettres pour « {service.name} ».")

        if cleaned.get('aid_requested'):
            if not cleaned.get('aid_amount'):
                self.add_error('aid_amount', 'Indiquez le montant demandé.')
            if not (cleaned.get('aid_reason') or '').strip():
                self.add_error('aid_reason', 'Indiquez le motif de la demande.')
        return cleaned

    def error_summary(self):
        """Erreurs à afficher en haut de page, préfixées du service concerné."""
        labels = {f'{s.pk}': s.name for s in self.services}
        labels.update({f'{s.pk}_sessions': s.name for s in self.services})
        labels.update({f'{s.pk}_details': s.name for s in self.services})
        labels.update({'aid_amount': 'Aide financière', 'aid_reason': 'Aide financière'})
        summary = []
        for name, errors in self.errors.items():
            prefix = labels.get(name)
            for error in errors:
                summary.append(f"{prefix} : {error}" if prefix and not error.startswith(prefix) else error)
        return summary

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
                    sessions=list(self.cleaned_data.get(f'{service.pk}_sessions') or []),
                    tickets=self.cleaned_data.get(f'{service.pk}_tickets')))
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
            'default_tickets', 'max_bookings_per_week', 'session_capacity', 'capacity_unit',
            'max_adults_per_booking', 'max_children_per_booking',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = CHECKBOX_CLASSES
            else:
                field.widget.attrs['class'] = INPUT_CLASSES



class SlotForm(forms.ModelForm):
    class Meta:
        model = ServiceScheduleSlot
        fields = ['weekday', 'start_time', 'end_time', 'capacity']
        widgets = {
            'weekday': forms.Select(attrs={'class': INPUT_CLASSES}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': INPUT_CLASSES}, format='%H:%M'),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': INPUT_CLASSES}, format='%H:%M'),
            'capacity': forms.NumberInput(attrs={'class': INPUT_CLASSES, 'min': 0, 'placeholder': '18'}),
        }


class SessionEditForm(forms.Form):
    """Modification d'une seule session (comme une occurrence de rendez-vous récurrent)."""
    date = TolerantDateField(label='Date')
    start_time = forms.TimeField(required=False, label='Début',
                                 widget=forms.TimeInput(attrs={'type': 'time', 'class': INPUT_CLASSES}, format='%H:%M'))
    end_time = forms.TimeField(required=False, label='Fin',
                               widget=forms.TimeInput(attrs={'type': 'time', 'class': INPUT_CLASSES}, format='%H:%M'))
    capacity = forms.IntegerField(required=False, min_value=0, label='Jauge',
                                  widget=forms.NumberInput(attrs={'class': INPUT_CLASSES, 'placeholder': '18'}))
    apply_to_following = forms.BooleanField(
        required=False, label='Appliquer cette jauge aux sessions suivantes de ce créneau',
        widget=forms.CheckboxInput(attrs={'class': CHECKBOX_CLASSES}))
    notes = forms.CharField(required=False, label='Notes', widget=forms.TextInput(attrs={'class': INPUT_CLASSES}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].widget.attrs['class'] = INPUT_CLASSES


class AdhocSessionForm(forms.Form):
    date = TolerantDateField(label='Date')
    start_time = forms.TimeField(required=False, label='Début',
                                 widget=forms.TimeInput(attrs={'type': 'time', 'class': INPUT_CLASSES}))
    end_time = forms.TimeField(required=False, label='Fin',
                               widget=forms.TimeInput(attrs={'type': 'time', 'class': INPUT_CLASSES}))
    capacity = forms.IntegerField(required=False, min_value=0, label='Jauge',
                                  widget=forms.NumberInput(attrs={'class': INPUT_CLASSES, 'placeholder': '18'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].widget.attrs['class'] = INPUT_CLASSES

    def clean_date(self):
        from django.utils import timezone
        value = self.cleaned_data['date']
        if value < timezone.localdate():
            raise forms.ValidationError('La date est passée.')
        return value


class AddFamilyToSessionForm(forms.Form):
    beneficiary = forms.ModelChoiceField(queryset=None, label='Famille',
                                         widget=forms.Select(attrs={'class': INPUT_CLASSES}))

    def __init__(self, *args, **kwargs):
        from beneficiaries.models import Beneficiary
        super().__init__(*args, **kwargs)
        self.fields['beneficiary'].queryset = Beneficiary.objects.order_by('last_name', 'first_name')
