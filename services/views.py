from collections import OrderedDict
from datetime import date, timedelta

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
    AidDecisionForm, AidPaymentForm, ServiceForm, SlotForm, SessionEditForm, AdhocSessionForm,
    AddFamilyToSessionForm,
)
from .models import (
    Service, ServiceScheduleSlot, ServiceSession, ServiceRegistration, ServiceBooking, FinancialAidRequest,
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
        logic.ensure_sessions(service)
        next_sessions = service.sessions.filter(date__gte=today).order_by('date', 'start_time')[:4]
        last_sessions = service.sessions.filter(date__lt=today).order_by('-date', '-start_time')[:3]
        distributions.append({'service': service, 'next_sessions': next_sessions, 'last_sessions': last_sessions})
    pending = FinancialAidRequest.objects.filter(status=FinancialAidRequest.STATUS_PENDING)
    approved_unpaid = FinancialAidRequest.objects.filter(status=FinancialAidRequest.STATUS_APPROVED)
    return render(request, 'services/home.html', {
        'distributions': distributions,
        'pending_count': pending.count(),
        'approved_unpaid_count': approved_unpaid.count(),
    })


# Planning d'un service de distribution : vue semaine, créneaux récurrents, sessions

def _parse_week(value, today):
    try:
        day = date.fromisoformat(value)
    except (TypeError, ValueError):
        day = today
    return logic.week_start(day)


@login_required
def week_view(request, service_pk):
    denied = _admin_required(request)
    if denied:
        return denied
    service = get_object_or_404(Service, pk=service_pk, kind=Service.KIND_DISTRIBUTION)
    today = timezone.localdate()
    monday = _parse_week(request.GET.get('week'), today)
    logic.ensure_sessions(service, until=max(monday + timedelta(days=6), today + timedelta(weeks=logic.HORIZON_WEEKS)))
    sessions = list(service.sessions.filter(date__gte=monday, date__lt=monday + timedelta(days=7))
                    .order_by('date', 'start_time'))
    days = []
    for i in range(7):
        day = monday + timedelta(days=i)
        days.append({'date': day, 'is_today': day == today, 'is_past': day < today,
                     'sessions': [s for s in sessions if s.date == day]})
    return render(request, 'services/week.html', {
        'service': service,
        'monday': monday,
        'sunday': monday + timedelta(days=6),
        'prev_week': (monday - timedelta(weeks=1)).isoformat(),
        'next_week': (monday + timedelta(weeks=1)).isoformat(),
        'this_week': logic.week_start(today).isoformat(),
        'days': days,
        'slots': service.schedule_slots.filter(is_active=True),
        'slot_form': SlotForm(initial={'capacity': service.session_capacity}),
        'adhoc_form': AdhocSessionForm(initial={'date': monday if monday >= today else today,
                                                'capacity': service.session_capacity}),
    })


def _week_redirect(service, day):
    return redirect(f"{reverse('services:week', args=[service.pk])}?week={logic.week_start(day).isoformat()}")


@login_required
@require_POST
def slot_save(request, service_pk, pk=None):
    denied = _admin_required(request)
    if denied:
        return denied
    service = get_object_or_404(Service, pk=service_pk, kind=Service.KIND_DISTRIBUTION)
    instance = get_object_or_404(ServiceScheduleSlot, pk=pk, service=service) if pk else None
    previous = ServiceScheduleSlot.objects.get(pk=pk) if pk else None
    form = SlotForm(request.POST, instance=instance)
    if form.is_valid():
        slot = form.save(commit=False)
        slot.service = service
        logic.save_slot(slot, previous=previous)
        messages.success(request, f"Créneau du {slot.get_weekday_display().lower()} enregistré : "
                                  f"les sessions à venir sont mises à jour.")
    else:
        messages.error(request, 'Créneau invalide : ' + '; '.join(
            f"{e}" for errors in form.errors.values() for e in errors))
    return redirect(f"{reverse('services:week', args=[service.pk])}?week={request.POST.get('week', '')}")


@login_required
@require_POST
def slot_delete(request, service_pk, pk):
    denied = _admin_required(request)
    if denied:
        return denied
    slot = get_object_or_404(ServiceScheduleSlot, pk=pk, service_id=service_pk)
    logic.delete_slot(slot)
    messages.success(request, f"Créneau du {slot.get_weekday_display().lower()} supprimé. "
                              f"Les sessions qui avaient déjà des inscrits sont conservées.")
    return redirect(f"{reverse('services:week', args=[service_pk])}?week={request.POST.get('week', '')}")


@login_required
@require_POST
def session_add(request, service_pk):
    denied = _admin_required(request)
    if denied:
        return denied
    service = get_object_or_404(Service, pk=service_pk, kind=Service.KIND_DISTRIBUTION)
    form = AdhocSessionForm(request.POST)
    if form.is_valid():
        session = logic.add_adhoc_session(service, form.cleaned_data['date'], form.cleaned_data['start_time'],
                                          form.cleaned_data['end_time'], form.cleaned_data['capacity'])
        messages.success(request, f"Session ajoutée le {session.date:%d/%m/%Y}.")
        return _week_redirect(service, session.date)
    messages.error(request, 'Session invalide : ' + '; '.join(
        f"{e}" for errors in form.errors.values() for e in errors))
    return redirect('services:week', service_pk=service.pk)


@login_required
def session_edit(request, pk):
    denied = _admin_required(request)
    if denied:
        return denied
    session = get_object_or_404(ServiceSession.objects.select_related('service', 'schedule_slot'), pk=pk)
    if request.method == 'POST':
        form = SessionEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            logic.update_session(session, date=data['date'], start_time=data['start_time'],
                                 end_time=data['end_time'], capacity=data['capacity'], notes=data['notes'],
                                 apply_to_following=data['apply_to_following'])
            messages.success(request, 'Session modifiée.')
            return _week_redirect(session.service, session.date)
    else:
        form = SessionEditForm(initial={
            'date': session.date, 'start_time': session.start_time, 'end_time': session.end_time,
            'capacity': session.capacity, 'notes': session.notes,
        })
    return render(request, 'services/session_edit.html', {
        'session': session, 'service': session.service, 'form': form,
        'booked': session.active_bookings().count(),
    })


@login_required
@require_POST
def session_toggle(request, pk):
    """Annule une session (les familles inscrites récupèrent leur passage) ou la rétablit."""
    denied = _admin_required(request)
    if denied:
        return denied
    session = get_object_or_404(ServiceSession.objects.select_related('service'), pk=pk)
    if session.is_closed:
        session.is_closed = False
        session.save(update_fields=['is_closed'])
        messages.success(request, f"Session du {session.date:%d/%m} rétablie.")
    else:
        with transaction.atomic():
            bookings = list(session.bookings.select_related('registration__beneficiary'))
            names = [b.registration.beneficiary.full_name for b in bookings]
            for booking in bookings:
                registration = booking.registration
                booking.delete()
                registration.refresh_status()
            session.is_closed = True
            session.is_customized = True
            session.save(update_fields=['is_closed', 'is_customized'])
        msg = f"Session du {session.date:%d/%m} annulée."
        if names:
            msg += " Familles à prévenir (passage rendu) : " + ', '.join(names) + '.'
        messages.warning(request, msg)
    return _week_redirect(session.service, session.date)


def _session_rows(session):
    bookings = (session.bookings.exclude(registration__status=ServiceRegistration.STATUS_CANCELLED)
                .select_related('registration__beneficiary', 'registration__interaction')
                .order_by('registration__beneficiary__last_name', 'registration__beneficiary__first_name'))
    rows = []
    for booking in bookings:
        reg = booking.registration
        ordered = list(reg.bookings.order_by('session__date', 'session__start_time')
                       .values_list('session_id', flat=True))
        rows.append({
            'booking': booking,
            'beneficiary': reg.beneficiary,
            'rank': ordered.index(session.pk) + 1 if session.pk in ordered else None,
            'total': reg.tickets,
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
        elif action == 'add_family':
            form = AddFamilyToSessionForm(request.POST)
            if form.is_valid():
                beneficiary = form.cleaned_data['beneficiary']
                try:
                    with transaction.atomic():
                        registration = logic.active_registration(beneficiary, session.service)
                        if registration is None or registration.tickets_left <= 0:
                            registration = ServiceRegistration.objects.create(
                                beneficiary=beneficiary, service=session.service, created_by=request.user,
                                details='Ajout manuel sur la liste', tickets=1)
                        logic.book(registration, session, request.user)
                    messages.success(request, f'{beneficiary.full_name} ajouté(e) à la liste.')
                except logic.RegistrationError as exc:
                    messages.error(request, str(exc))
        elif action == 'remove':
            booking = get_object_or_404(ServiceBooking, pk=request.POST.get('booking'), session=session)
            registration = booking.registration
            booking.delete()
            registration.refresh_status()
            messages.success(request, 'Famille retirée de la liste : son passage est rendu.')
        return redirect('services:session_detail', pk=session.pk)

    template = 'services/session_print.html' if request.GET.get('print') else 'services/session_detail.html'
    return render(request, template, {
        'session': session,
        'service': session.service,
        'rows': rows,
        'totals': _session_totals(rows),
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
def booking_assign(request, pk):
    """Place un passage restant de l'inscription sur une session (depuis la fiche)."""
    denied = _access_required(request)
    if denied:
        return denied
    registration = get_object_or_404(ServiceRegistration.objects.select_related('service'), pk=pk)
    session = get_object_or_404(ServiceSession, pk=request.POST.get('session'), service=registration.service)
    try:
        with transaction.atomic():
            logic.book(registration, session, request.user)
        messages.success(request, f"{registration.service.name} : réservé le {session.date:%d/%m}.")
    except logic.RegistrationError as exc:
        messages.error(request, str(exc))
    return redirect('beneficiaries:detail', pk=registration.beneficiary_id)


@login_required
@require_POST
def booking_cancel(request, pk):
    """Annule une réservation à venir : le passage redevient disponible."""
    denied = _access_required(request)
    if denied:
        return denied
    booking = get_object_or_404(ServiceBooking.objects.select_related('registration', 'session'), pk=pk)
    registration = booking.registration
    if booking.session.date < timezone.localdate() or booking.attended is not None:
        messages.error(request, 'Ce passage est déjà passé ou pointé.')
    else:
        booking.delete()
        registration.refresh_status()
        messages.success(request, 'Réservation annulée : le passage est de nouveau disponible.')
    return redirect('beneficiaries:detail', pk=registration.beneficiary_id)


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
