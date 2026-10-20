from collections import OrderedDict
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView

from . import logic
from .forms import (
    AidDecisionForm, AidPaymentForm, ServiceForm, SessionForm, AddFamilyToSessionForm,
)
from .models import (
    Service, ServiceSession, ServiceRegistration, ServiceBooking, FinancialAidRequest,
)
from .notifications import notify_decision
from .permissions import ServicesAdminMixin, can_use_services, is_services_admin


def _admin_required(request):
    if not is_services_admin(request.user):
        messages.error(request, 'Cette action est réservée aux administrateurs et salariés.')
        return redirect('home')
    return None


def _access_required(request):
    if not can_use_services(request.user):
        messages.error(request, "Vous n'avez pas accès aux services aux bénéficiaires.")
        return redirect('home')
    return None


# Tableau de bord des services

@login_required
def services_home(request):
    denied = _admin_required(request)
    if denied:
        return denied
    today = timezone.localdate()
    distributions = []
    for service in Service.objects.filter(is_active=True, kind=Service.KIND_DISTRIBUTION):
        logic.upcoming_sessions(service, count=1)  # crée la prochaine session si besoin
        next_sessions = service.sessions.filter(date__gte=today).order_by('date')[:3]
        last_sessions = service.sessions.filter(date__lt=today).order_by('-date')[:3]
        distributions.append({'service': service, 'next_sessions': next_sessions, 'last_sessions': last_sessions})
    pending = FinancialAidRequest.objects.filter(status=FinancialAidRequest.STATUS_PENDING)
    approved_unpaid = FinancialAidRequest.objects.filter(status=FinancialAidRequest.STATUS_APPROVED)
    return render(request, 'services/home.html', {
        'distributions': distributions,
        'pending_count': pending.count(),
        'approved_unpaid_count': approved_unpaid.count(),
        'recent_pending': pending.select_related('beneficiary', 'requested_by')[:5],
    })


# Sessions de distribution

@login_required
def session_list(request, service_pk):
    denied = _admin_required(request)
    if denied:
        return denied
    service = get_object_or_404(Service, pk=service_pk, kind=Service.KIND_DISTRIBUTION)
    logic.upcoming_sessions(service, count=4)
    today = timezone.localdate()
    return render(request, 'services/session_list.html', {
        'service': service,
        'upcoming': service.sessions.filter(date__gte=today).order_by('date')[:8],
        'past': service.sessions.filter(date__lt=today).order_by('-date')[:12],
    })


def _session_rows(session):
    bookings = (session.bookings.exclude(registration__status=ServiceRegistration.STATUS_CANCELLED)
                .select_related('registration__beneficiary', 'registration__interaction')
                .order_by('registration__beneficiary__last_name', 'registration__beneficiary__first_name'))
    rows = []
    for booking in bookings:
        reg = booking.registration
        all_bookings = list(reg.bookings.order_by('session__date').values_list('session_id', flat=True))
        rows.append({
            'booking': booking,
            'beneficiary': reg.beneficiary,
            'rank': all_bookings.index(session.pk) + 1 if session.pk in all_bookings else None,
            'total': len(all_bookings),
            'interview_date': reg.interaction.created_at if reg.interaction else reg.created_at,
        })
    return rows


def _session_totals(rows):
    totals = {'families': len(rows), 'adults': 0, 'children': 0, 'babies': 0,
              'present': 0, 'absent': 0, 'unknown': 0}
    for row in rows:
        b = row['booking']
        totals['adults'] += b.adults
        totals['children'] += b.children
        totals['babies'] += b.babies
        key = 'present' if b.attended else 'absent' if b.attended is False else 'unknown'
        totals[key] += 1
    return totals


@login_required
def session_detail(request, pk):
    denied = _admin_required(request)
    if denied:
        return denied
    session = get_object_or_404(ServiceSession.objects.select_related('service'), pk=pk)
    rows = _session_rows(session)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'attendance':
            with transaction.atomic():
                for row in rows:
                    booking = row['booking']
                    value = request.POST.get(f'attended_{booking.pk}', '')
                    attended = True if value == 'yes' else False if value == 'no' else None
                    obs = request.POST.get(f'obs_{booking.pk}', booking.observations).strip()[:300]
                    if obs != booking.observations:
                        booking.observations = obs
                        booking.save(update_fields=['observations'])
                    if attended != booking.attended:
                        booking.mark(attended, request.user)
            messages.success(request, 'Présences enregistrées.')
        elif action == 'settings':
            form = SessionForm(request.POST, instance=session)
            if form.is_valid():
                form.save()
                messages.success(request, 'Session mise à jour.')
        elif action == 'add_family':
            form = AddFamilyToSessionForm(request.POST)
            if form.is_valid():
                beneficiary = form.cleaned_data['beneficiary']
                composition = logic.household_composition(beneficiary)
                if session.bookings.filter(registration__beneficiary=beneficiary).exclude(
                        registration__status=ServiceRegistration.STATUS_CANCELLED).exists():
                    messages.warning(request, f'{beneficiary.full_name} est déjà sur cette liste.')
                else:
                    reg = ServiceRegistration.objects.create(
                        beneficiary=beneficiary, service=session.service, created_by=request.user,
                        details='Ajout manuel sur la liste')
                    ServiceBooking.objects.create(
                        registration=reg, session=session, adults=composition.adults,
                        children=composition.children, babies=composition.babies)
                    messages.success(request, f'{beneficiary.full_name} ajouté(e) à la liste.')
        elif action == 'remove':
            booking = get_object_or_404(ServiceBooking, pk=request.POST.get('booking'), session=session)
            reg = booking.registration
            booking.delete()
            if not reg.bookings.exists():
                reg.status = ServiceRegistration.STATUS_CANCELLED
                reg.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Famille retirée de la liste.')
        return redirect('services:session_detail', pk=session.pk)

    template = 'services/session_print.html' if request.GET.get('print') else 'services/session_detail.html'
    return render(request, template, {
        'session': session,
        'service': session.service,
        'rows': rows,
        'totals': _session_totals(rows),
        'settings_form': SessionForm(instance=session),
        'add_form': AddFamilyToSessionForm(),
    })


# Actions depuis la fiche bénéficiaire

@login_required
@require_POST
def booking_mark(request, pk):
    denied = _access_required(request)
    if denied:
        return denied
    booking = get_object_or_404(ServiceBooking.objects.select_related('registration'), pk=pk)
    value = request.POST.get('attended')
    booking.mark(True if value == 'yes' else False if value == 'no' else None, request.user)
    messages.success(request, f'Passage {booking.session.service.name} enregistré.')
    return redirect('beneficiaries:detail', pk=booking.registration.beneficiary_id)


@login_required
@require_POST
def registration_cancel(request, pk):
    denied = _access_required(request)
    if denied:
        return denied
    reg = get_object_or_404(ServiceRegistration, pk=pk)
    with transaction.atomic():
        reg.bookings.filter(attended__isnull=True).delete()
        reg.status = ServiceRegistration.STATUS_CANCELLED
        reg.save(update_fields=['status', 'updated_at'])
    messages.success(request, f'Inscription {reg.service.name} annulée.')
    return redirect('beneficiaries:detail', pk=reg.beneficiary_id)


@login_required
@require_POST
def registration_done(request, pk):
    denied = _access_required(request)
    if denied:
        return denied
    reg = get_object_or_404(ServiceRegistration, pk=pk)
    reg.status = ServiceRegistration.STATUS_DONE
    reg.save(update_fields=['status', 'updated_at'])
    messages.success(request, f'{reg.service.name} marqué comme réalisé.')
    return redirect('beneficiaries:detail', pk=reg.beneficiary_id)


@login_required
def registration_voucher(request, pk):
    denied = _access_required(request)
    if denied:
        return denied
    reg = get_object_or_404(ServiceRegistration.objects.select_related('service__partner', 'beneficiary'), pk=pk)
    return render(request, 'services/voucher.html', {'registration': reg, 'today': timezone.localdate()})


# Aides financières

@login_required
def aid_list(request):
    denied = _admin_required(request)
    if denied:
        return denied
    status = request.GET.get('status', FinancialAidRequest.STATUS_PENDING)
    aids = FinancialAidRequest.objects.select_related('beneficiary', 'requested_by', 'decided_by')
    if status != 'ALL':
        aids = aids.filter(status=status)
    counts = dict(FinancialAidRequest.objects.values_list('status').annotate(n=Count('id')))
    tabs = [(code, label, counts.get(code, 0)) for code, label in FinancialAidRequest.STATUS_CHOICES]
    return render(request, 'services/aid_list.html', {
        'aids': aids[:200], 'status': status, 'tabs': tabs,
    })


@login_required
def aid_detail(request, pk):
    denied = _admin_required(request)
    if denied:
        return denied
    aid = get_object_or_404(FinancialAidRequest.objects.select_related('beneficiary', 'requested_by'), pk=pk)
    decision_form = AidDecisionForm()
    payment_form = AidPaymentForm(instance=aid, initial={'paid_at': timezone.localdate()})

    if request.method == 'POST':
        if request.POST.get('action') == 'decide' and aid.status == FinancialAidRequest.STATUS_PENDING:
            decision_form = AidDecisionForm(request.POST)
            if decision_form.is_valid():
                aid.status = decision_form.cleaned_data['decision']
                aid.rejection_reason = (decision_form.cleaned_data.get('rejection_reason') or '').strip() \
                    if aid.status == FinancialAidRequest.STATUS_REJECTED else ''
                aid.decided_by = request.user
                aid.decided_at = timezone.now()
                aid.save()
                notify_decision(aid)
                messages.success(request, f'Demande {aid.get_status_display().lower()}.')
                return redirect('services:aid_detail', pk=aid.pk)
        elif request.POST.get('action') == 'pay' and aid.status == FinancialAidRequest.STATUS_APPROVED:
            payment_form = AidPaymentForm(request.POST, instance=aid)
            if payment_form.is_valid():
                aid = payment_form.save(commit=False)
                aid.status = FinancialAidRequest.STATUS_PAID
                aid.paid_by = request.user
                aid.save()
                messages.success(request, 'Versement enregistré.')
                return redirect('services:aid_detail', pk=aid.pk)

    beneficiary = aid.beneficiary
    return render(request, 'services/aid_detail.html', {
        'aid': aid,
        'beneficiary': beneficiary,
        'latest_snapshot': beneficiary.latest_financial_snapshot,
        'history': beneficiary.financial_aid_requests.exclude(pk=aid.pk)[:10],
        'composition': logic.household_composition(beneficiary),
        'decision_form': decision_form,
        'payment_form': payment_form,
    })


# Catalogue

class ServiceListView(ServicesAdminMixin, ListView):
    model = Service
    template_name = 'services/catalogue.html'
    context_object_name = 'services'


class ServiceCreateView(ServicesAdminMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'services/service_form.html'

    def get_success_url(self):
        messages.success(self.request, 'Service créé.')
        return reverse('services:catalogue')


class ServiceUpdateView(ServicesAdminMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'services/service_form.html'

    def get_success_url(self):
        messages.success(self.request, 'Service mis à jour.')
        return reverse('services:catalogue')


# Statistiques

PERIODS = OrderedDict([('month', 'Mensuel'), ('quarter', 'Trimestriel'), ('year', 'Annuel')])


def _period_bounds(period, year, index):
    if period == 'year':
        return date(year, 1, 1), date(year + 1, 1, 1)
    if period == 'quarter':
        start_month = 3 * (index - 1) + 1
        end = date(year + 1, 1, 1) if start_month == 10 else date(year, start_month + 3, 1)
        return date(year, start_month, 1), end
    end = date(year + 1, 1, 1) if index == 12 else date(year, index + 1, 1)
    return date(year, index, 1), end


def distribution_stats(service, start, end):
    bookings = ServiceBooking.objects.filter(
        session__service=service, session__date__gte=start, session__date__lt=end,
    ).exclude(registration__status=ServiceRegistration.STATUS_CANCELLED)
    served = bookings.filter(attended=True)
    agg = served.aggregate(a=Sum('adults'), c=Sum('children'), b=Sum('babies'))
    return {
        'service': service,
        'sessions': ServiceSession.objects.filter(service=service, date__gte=start, date__lt=end,
                                                  bookings__isnull=False).distinct().count(),
        'registered': bookings.count(),
        'served': served.count(),
        'absent': bookings.filter(attended=False).count(),
        'not_recorded': bookings.filter(attended__isnull=True).count(),
        'distinct_families': served.values('registration__beneficiary').distinct().count(),
        'adults': agg['a'] or 0,
        'children': agg['c'] or 0,
        'babies': agg['b'] or 0,
        'new_registrations': ServiceRegistration.objects.filter(
            service=service, created_at__date__gte=start, created_at__date__lt=end).count(),
    }


def aid_stats(start, end):
    decided = FinancialAidRequest.objects.filter(
        status__in=[FinancialAidRequest.STATUS_APPROVED, FinancialAidRequest.STATUS_PAID],
        decided_at__date__gte=start, decided_at__date__lt=end)
    labels = dict(FinancialAidRequest.NATURE_CHOICES)
    by_nature = [
        {'nature': labels.get(row['nature'], row['nature']), 'count': row['n'], 'amount': row['total']}
        for row in decided.values('nature').annotate(n=Count('id'), total=Sum('amount')).order_by('-total')
    ]
    requested = FinancialAidRequest.objects.filter(created_at__date__gte=start, created_at__date__lt=end)
    return {
        'requested': requested.count(),
        'rejected': FinancialAidRequest.objects.filter(
            status=FinancialAidRequest.STATUS_REJECTED, decided_at__date__gte=start,
            decided_at__date__lt=end).count(),
        'granted': decided.count(),
        'granted_amount': decided.aggregate(s=Sum('amount'))['s'] or 0,
        'paid_amount': FinancialAidRequest.objects.filter(
            status=FinancialAidRequest.STATUS_PAID, paid_at__gte=start, paid_at__lt=end,
        ).aggregate(s=Sum('amount'))['s'] or 0,
        'by_nature': by_nature,
    }


def simple_stats(start, end):
    return (ServiceRegistration.objects
            .filter(created_at__date__gte=start, created_at__date__lt=end,
                    service__kind=Service.KIND_SIMPLE)
            .exclude(status=ServiceRegistration.STATUS_CANCELLED)
            .values('service__name', 'service__category')
            .annotate(n=Count('id'), families=Count('beneficiary', distinct=True))
            .order_by('service__category', '-n'))


@login_required
def stats(request):
    denied = _admin_required(request)
    if denied:
        return denied
    today = timezone.localdate()
    period = request.GET.get('period', 'month')
    if period not in PERIODS:
        period = 'month'
    try:
        year = int(request.GET.get('year', today.year))
    except ValueError:
        year = today.year
    default_index = today.month if period == 'month' else (today.month - 1) // 3 + 1
    try:
        index = int(request.GET.get('index', default_index))
    except ValueError:
        index = default_index
    index = max(1, min(index, 12 if period == 'month' else 4))
    start, end = _period_bounds(period, year, index)

    return render(request, 'services/stats.html', {
        'period': period, 'periods': PERIODS, 'year': year, 'index': index,
        'years': range(today.year - 4, today.year + 1),
        'indexes': range(1, 13) if period == 'month' else range(1, 5),
        'start': start, 'end': end,
        'distribution_stats': [distribution_stats(s, start, end)
                               for s in Service.objects.filter(kind=Service.KIND_DISTRIBUTION)],
        'aid': aid_stats(start, end),
        'simple': simple_stats(start, end),
    })
