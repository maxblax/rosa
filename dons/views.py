from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView, ListView
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta
from itertools import groupby
from operator import itemgetter
from collections import defaultdict

from volunteers.permissions import AdminOrEmployeeRequiredMixin
from .models import Donation
from .forms import donationForm
from .services import helloasso_service


class donationListView(AdminOrEmployeeRequiredMixin, ListView):
    """
    Vue principale listant TOUS les dons (manuels + HelloAsso)
    avec statistiques et groupement par mois
    """
    model = Donation
    template_name = 'dons/donation_list.html'
    context_object_name = 'manual_donations'

    def get_queryset(self):
        """Récupère les dons manuels de la base de données"""
        return Donation.objects.select_related('created_by').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Récupérer tous les dons (manuels + HelloAsso)
        all_donations = self._get_all_donations()

        # Grouper par mois
        donations_by_month = self._group_by_month(all_donations)

        # Calculer les statistiques
        stats = self._calculate_statistics(all_donations)

        context['donations_by_month'] = donations_by_month
        context['stats'] = stats
        context['helloasso_enabled'] = helloasso_service.is_enabled()

        return context

    def _get_all_donations(self):
        """Fusionne les dons manuels et HelloAsso, triés anti-chronologiquement"""
        donations = []

        # Ajouter les dons manuels
        for donation in self.get_queryset():
            donations.append({
                'id': donation.pk,
                'donor_name': donation.donor_name if not donation.is_anonymous else None,
                'amount': float(donation.amount),
                'date': donation.date,
                'datetime': datetime.combine(donation.date, time.min),
                'is_anonymous': donation.is_anonymous,
                'payment_type': donation.get_payment_type_display(),
                'source': 'Manuel',
                'notes': donation.notes or '',
                'can_edit': True,  # Les dons manuels peuvent être édités
                'object': donation,  # Référence à l'objet Django pour les URLs
            })

        # Ajouter les dons HelloAsso (si activé)
        if helloasso_service.is_enabled():
            try:
                helloasso_donations = helloasso_service.get_donations()
                for donation in helloasso_donations:
                    # Convertir datetime aware en naive pour la comparaison
                    dt = donation.get('datetime')
                    if dt and dt.tzinfo is not None:
                        dt = dt.replace(tzinfo=None)

                    donations.append({
                        'id': donation.get('id'),
                        'donor_name': donation.get('donor_name'),
                        'amount': donation.get('amount', 0),
                        'date': donation.get('date'),
                        'datetime': dt,
                        'is_anonymous': donation.get('is_anonymous', False),
                        'payment_type': 'HelloAsso',
                        'source': 'HelloAsso',
                        'notes': donation.get('notes', ''),
                        'can_edit': False,  # Les dons HelloAsso ne peuvent PAS être édités
                        'object': None,
                    })
            except Exception as e:
                messages.warning(
                    self.request,
                    f"Impossible de récupérer les dons HelloAsso: {e}"
                )

        # Trier par date décroissante (plus récent en premier)
        donations.sort(key=lambda x: x['datetime'] if x['datetime'] else datetime.min, reverse=True)

        return donations

    def _group_by_month(self, donations):
        """Groupe les dons par mois"""
        # Grouper par année et mois
        def get_month_key(donation):
            date = donation.get('date')
            if not date:
                return (9999, 99)  # Mettre les dons sans date à la fin
            return (date.year, date.month)

        # Trier par mois décroissant
        sorted_donations = sorted(donations, key=get_month_key, reverse=True)

        # Grouper
        grouped = []
        for (year, month), items in groupby(sorted_donations, key=get_month_key):
            if year == 9999:
                month_name = "Date inconnue"
                month_date = None
            else:
                month_name = None  # Sera formaté dans le template
                month_date = datetime(year, month, 1).date()

            items_list = list(items)
            total = sum(item['amount'] for item in items_list)

            grouped.append({
                'month_name': month_name,
                'month_date': month_date,
                'donations': items_list,
                'total': total,
                'count': len(items_list)
            })

        return grouped

    def _calculate_statistics(self, donations):
        """Calcule les statistiques sur différentes périodes"""
        now = datetime.now()
        one_month_ago = now - relativedelta(months=1)
        six_months_ago = now - relativedelta(months=6)
        one_year_ago = now - relativedelta(years=1)

        stats = {
            'last_month': {'total': 0, 'count': 0},
            'last_6_months': {'total': 0, 'count': 0},
            'last_year': {'total': 0, 'count': 0},
            'all_time': {'total': 0, 'count': 0},
        }

        for donation in donations:
            date = donation.get('date')
            if not date:
                continue

            amount = donation.get('amount', 0)
            donation_datetime = datetime.combine(date, time.min)

            # Statistiques par période
            if donation_datetime >= one_month_ago:
                stats['last_month']['total'] += amount
                stats['last_month']['count'] += 1

            if donation_datetime >= six_months_ago:
                stats['last_6_months']['total'] += amount
                stats['last_6_months']['count'] += 1

            if donation_datetime >= one_year_ago:
                stats['last_year']['total'] += amount
                stats['last_year']['count'] += 1

            # All time
            stats['all_time']['total'] += amount
            stats['all_time']['count'] += 1

        return stats


class donationCreateView(AdminOrEmployeeRequiredMixin, CreateView):
    """Créer un don manuel"""
    model = Donation
    form_class = donationForm
    template_name = 'dons/donation_form.html'
    success_url = reverse_lazy('dons:list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Don enregistré avec succès.')
        return super().form_valid(form)


class donationUpdateView(AdminOrEmployeeRequiredMixin, UpdateView):
    """Modifier un don manuel"""
    model = Donation
    form_class = donationForm
    template_name = 'dons/donation_form.html'
    success_url = reverse_lazy('dons:list')

    def form_valid(self, form):
        messages.success(self.request, 'Don modifié avec succès.')
        return super().form_valid(form)


class donationDetailView(AdminOrEmployeeRequiredMixin, DetailView):
    """Voir les détails d'un don manuel"""
    model = Donation
    template_name = 'dons/donation_detail.html'
    context_object_name = 'donation'


class donationDeleteView(AdminOrEmployeeRequiredMixin, DeleteView):
    """Supprimer un don manuel"""
    model = Donation
    template_name = 'dons/donation_confirm_delete.html'
    success_url = reverse_lazy('dons:list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Don supprimé avec succès.')
        return super().delete(request, *args, **kwargs)


class DrosatirosanalyticsView(AdminOrEmployeeRequiredMixin, ListView):
    """Vue d'analyse financière des dons"""
    model = Donation
    template_name = 'dons/donation_analytics.html'
    context_object_name = 'donations'

    def get_queryset(self):
        """Récupère les dons manuels de la base de données"""
        return Donation.objects.select_related('created_by').all()

    def get_context_data(self, **kwargs):
        import json
        context = super().get_context_data(**kwargs)

        # Récupérer tous les dons (manuels + HelloAsso)
        all_donations = self._get_all_donations()

        # Analyses
        monthly_data = self._get_monthly_analysis(all_donations)
        yearly_comparison = self._get_yearly_comparison(all_donations)

        # Convertir by_month en dict simple pour JSON
        yearly_comparison['current']['by_month'] = dict(yearly_comparison['current']['by_month'])
        yearly_comparison['last']['by_month'] = dict(yearly_comparison['last']['by_month'])

        context['monthly_data'] = json.dumps(monthly_data)
        context['yearly_comparison'] = yearly_comparison
        context['donor_distribution'] = self._get_donor_distribution(all_donations)
        context['helloasso_enabled'] = helloasso_service.is_enabled()

        return context

    def _get_all_donations(self):
        """Fusionne les dons manuels et HelloAsso"""
        donations = []

        # Ajouter les dons manuels
        for donation in self.get_queryset():
            donations.append({
                'donor_name': donation.donor_name if not donation.is_anonymous else 'Anonyme',
                'amount': float(donation.amount),
                'date': donation.date,
                'is_anonymous': donation.is_anonymous,
                'source': 'Manuel',
            })

        # Ajouter les dons HelloAsso (si activé)
        if helloasso_service.is_enabled():
            try:
                helloasso_donations = helloasso_service.get_donations()
                for donation in helloasso_donations:
                    donations.append({
                        'donor_name': donation.get('donor_name') or 'Anonyme',
                        'amount': donation.get('amount', 0),
                        'date': donation.get('date'),
                        'is_anonymous': donation.get('is_anonymous', False),
                        'source': 'HelloAsso',
                    })
            except Exception:
                pass

        return donations

    def _get_monthly_analysis(self, donations):
        """Analyse des dons par mois sur les 12 derniers mois"""
        now = datetime.now()
        monthly_totals = defaultdict(lambda: {'amount': 0, 'count': 0})

        # Calculer pour les 12 derniers mois
        for i in range(12):
            month_date = now - relativedelta(months=i)
            key = month_date.strftime('%Y-%m')
            monthly_totals[key] = {'amount': 0, 'count': 0, 'month': month_date.month, 'year': month_date.year}

        for donation in donations:
            if donation.get('date'):
                key = donation['date'].strftime('%Y-%m')
                if key in monthly_totals:
                    monthly_totals[key]['amount'] += donation['amount']
                    monthly_totals[key]['count'] += 1

        # Trier par date
        return sorted(monthly_totals.values(), key=lambda x: (x['year'], x['month']))

    def _get_yearly_comparison(self, donations):
        """Compare l'année en cours avec l'année précédente"""
        now = datetime.now()
        current_year = now.year
        last_year = current_year - 1

        current_year_data = {'amount': 0, 'count': 0, 'by_month': defaultdict(lambda: {'amount': 0, 'count': 0})}
        last_year_data = {'amount': 0, 'count': 0, 'by_month': defaultdict(lambda: {'amount': 0, 'count': 0})}

        for donation in donations:
            if donation.get('date'):
                year = donation['date'].year
                month = donation['date'].month

                if year == current_year:
                    current_year_data['amount'] += donation['amount']
                    current_year_data['count'] += 1
                    current_year_data['by_month'][month]['amount'] += donation['amount']
                    current_year_data['by_month'][month]['count'] += 1
                elif year == last_year:
                    last_year_data['amount'] += donation['amount']
                    last_year_data['count'] += 1
                    last_year_data['by_month'][month]['amount'] += donation['amount']
                    last_year_data['by_month'][month]['count'] += 1

        return {
            'current_year': current_year,
            'last_year': last_year,
            'current': current_year_data,
            'last': last_year_data,
        }

    def _get_donor_distribution(self, donations):
        """Distribution par drosateur"""
        donor_stats = defaultdict(lambda: {'amount': 0, 'count': 0})

        for donation in donations:
            donor = donation.get('donor_name', 'Anonyme')
            donor_stats[donor]['amount'] += donation['amount']
            donor_stats[donor]['count'] += 1

        # Trier par montant total
        sorted_donors = sorted(
            [{'name': k, 'amount': v['amount'], 'count': v['count']} for k, v in donor_stats.items()],
            key=lambda x: x['amount'],
            reverse=True
        )

        return sorted_donors[:10]  # Top 10 drosateurs
