from datetime import date, time, timedelta
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from beneficiaries.models import Beneficiary, Child, HouseholdAdult
from volunteers.models import Volunteer
from . import logic
from .forms import InteractionServicesForm
from .models import (
    Service, ServiceScheduleSlot, ServiceSession, ServiceRegistration, ServiceBooking, FinancialAidRequest,
)

# Mardi 21/10/2025 : le mercredi suivant est le 22/10, le jeudi le 23/10.
TODAY = date(2025, 10, 21)


def make_beneficiary(adults=0, children_ages=(), dependents=0, name='DUPONT'):
    b = Beneficiary.objects.create(first_name='Marie', last_name=name, dependents_count=dependents,
                                   gdpr_consent=True)
    for i in range(adults):
        HouseholdAdult.objects.create(beneficiary=b, first_name=f'Adulte{i}')
    for i, age in enumerate(children_ages):
        Child.objects.create(beneficiary=b, first_name=f'Enfant{i}',
                             birth_date=TODAY - timedelta(days=365 * age + 30))
    return b


@mock.patch('django.utils.timezone.localdate', return_value=TODAY)
class CompositionTests(TestCase):
    def test_composition_from_records(self, _):
        b = make_beneficiary(adults=1, children_ages=(1, 5, 12))
        c = logic.household_composition(b)
        self.assertEqual((c.adults, c.children, c.babies), (2, 2, 1))

    def test_composition_falls_back_on_dependents_count(self, _):
        b = make_beneficiary(dependents=3)
        c = logic.household_composition(b)
        self.assertEqual((c.adults, c.children, c.babies), (1, 3, 0))


@mock.patch('services.logic.timezone.localdate', return_value=TODAY)
class ScheduleTests(TestCase):
    def setUp(self):
        patcher = mock.patch('services.logic.timezone.localdate', return_value=TODAY)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.grocery = Service.objects.get(name__startswith='Épicerie')
        self.wed = self.grocery.schedule_slots.get()

    def test_sessions_generated_from_several_weekly_openings(self, _):
        ServiceScheduleSlot.objects.create(service=self.grocery, weekday=1, start_time=time(9), capacity=10)
        ServiceScheduleSlot.objects.create(service=self.grocery, weekday=4, start_time=time(9), capacity=12)
        logic.ensure_sessions(self.grocery, until=date(2025, 10, 26))
        days = list(self.grocery.sessions.order_by('date').values_list('date', 'capacity'))
        self.assertEqual(days, [(date(2025, 10, 21), 10), (date(2025, 10, 22), 18), (date(2025, 10, 24), 12)])

    def test_new_session_copies_previous_capacity(self, _):
        logic.ensure_sessions(self.grocery, until=date(2025, 10, 22))
        first = self.grocery.sessions.get(date=date(2025, 10, 22))
        first.capacity = 25
        first.save()
        logic.ensure_sessions(self.grocery, until=date(2025, 10, 29))
        self.assertEqual(self.grocery.sessions.get(date=date(2025, 10, 29)).capacity, 25)

    def test_capacity_applied_to_following_sessions(self, _):
        logic.ensure_sessions(self.grocery, until=date(2025, 11, 12))
        first = self.grocery.sessions.get(date=date(2025, 10, 29))
        logic.update_session(first, date=first.date, start_time=first.start_time, end_time=first.end_time,
                             capacity=30, apply_to_following=True)
        caps = dict(self.grocery.sessions.values_list('date', 'capacity'))
        self.assertEqual(caps[date(2025, 10, 22)], 18)
        self.assertEqual(caps[date(2025, 11, 5)], 30)
        self.wed.refresh_from_db()
        self.assertEqual(self.wed.capacity, 30)

    def test_moved_session_is_not_regenerated(self, _):
        logic.ensure_sessions(self.grocery, until=date(2025, 10, 29))
        session = self.grocery.sessions.get(date=date(2025, 10, 22))
        logic.update_session(session, date=date(2025, 10, 23), start_time=session.start_time,
                             end_time=session.end_time, capacity=session.capacity)
        logic.ensure_sessions(self.grocery, until=date(2025, 10, 29))
        self.assertFalse(self.grocery.sessions.filter(date=date(2025, 10, 22)).exists())
        self.assertTrue(self.grocery.sessions.get(date=date(2025, 10, 23)).is_customized)

    def test_slot_weekday_change_moves_empty_future_sessions(self, _):
        logic.ensure_sessions(self.grocery)
        previous = ServiceScheduleSlot.objects.get(pk=self.wed.pk)
        self.wed.weekday = 0
        logic.save_slot(self.wed, previous=previous)
        weekdays = set(d.weekday() for d in self.grocery.sessions.values_list('date', flat=True))
        self.assertEqual(weekdays, {0})

    def test_adhoc_session(self, _):
        session = logic.add_adhoc_session(self.grocery, date(2025, 10, 25))
        self.assertEqual(session.capacity, 18)
        self.assertIsNone(session.schedule_slot)


@mock.patch('services.logic.timezone.localdate', return_value=TODAY)
class GroceryTicketTests(TestCase):
    def setUp(self):
        patcher = mock.patch('services.logic.timezone.localdate', return_value=TODAY)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.grocery = Service.objects.get(name__startswith='Épicerie')
        ServiceScheduleSlot.objects.create(service=self.grocery, weekday=4, start_time=time(9), capacity=18)
        logic.ensure_sessions(self.grocery)

    def s(self, day):
        return self.grocery.sessions.filter(date=day).first()

    def test_three_tickets_with_chosen_dates(self, _):
        b = make_beneficiary(adults=1, children_ages=(4,))
        reg = logic.register_distribution(b, self.grocery, sessions=[self.s(date(2025, 10, 22))])
        self.assertEqual((reg.tickets, reg.tickets_used, reg.tickets_left), (3, 1, 2))
        logic.book(reg, self.s(date(2025, 10, 31)))
        logic.book(reg, self.s(date(2025, 11, 5)))
        with self.assertRaises(logic.RegistrationError):
            logic.book(reg, self.s(date(2025, 11, 12)))

    def test_one_visit_per_week(self, _):
        reg = logic.register_distribution(make_beneficiary(), self.grocery, sessions=[self.s(date(2025, 10, 22))])
        with self.assertRaises(logic.RegistrationError):
            logic.book(reg, self.s(date(2025, 10, 24)))

    def test_more_dates_than_tickets_refused(self, _):
        with self.assertRaises(logic.RegistrationError):
            logic.register_distribution(make_beneficiary(), self.grocery, tickets=1, sessions=[
                self.s(date(2025, 10, 22)), self.s(date(2025, 10, 29))])

    def test_no_second_registration_while_active(self, _):
        b = make_beneficiary()
        logic.register_distribution(b, self.grocery)
        with self.assertRaises(logic.RegistrationError):
            logic.register_distribution(b, self.grocery)

    def test_done_when_all_tickets_used_and_recorded(self, _):
        reg = logic.register_distribution(make_beneficiary(), self.grocery, sessions=[
            self.s(date(2025, 10, 22)), self.s(date(2025, 10, 29)), self.s(date(2025, 11, 5))])
        bookings = list(reg.bookings.all())
        bookings[0].mark(True)
        bookings[1].mark(False)
        reg.refresh_from_db()
        self.assertEqual(reg.status, ServiceRegistration.STATUS_ACTIVE)
        bookings[2].mark(True)
        reg.refresh_from_db()
        self.assertEqual(reg.status, ServiceRegistration.STATUS_DONE)

    def test_cancelling_session_gives_ticket_back(self, _):
        reg = logic.register_distribution(make_beneficiary(), self.grocery, sessions=[self.s(date(2025, 10, 22))])
        self.assertEqual(reg.tickets_left, 2)
        self.s(date(2025, 10, 22)).bookings.all().delete()
        self.assertEqual(reg.tickets_left, 3)


@mock.patch('services.logic.timezone.localdate', return_value=TODAY)
class ClothingTests(TestCase):
    def setUp(self):
        patcher = mock.patch('services.logic.timezone.localdate', return_value=TODAY)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.clothing = Service.objects.get(name__startswith='Vestiaire')
        logic.ensure_sessions(self.clothing)

    def s(self, day=date(2025, 10, 23)):
        return self.clothing.sessions.get(date=day)

    def test_single_ticket(self, _):
        b = make_beneficiary(adults=1, children_ages=(6,))
        reg = logic.register_distribution(b, self.clothing, sessions=[self.s()])
        self.assertEqual((reg.tickets, reg.tickets_left), (1, 0))

    def test_large_family_gets_two_tickets_split(self, _):
        b = make_beneficiary(adults=2, children_ages=(2, 6, 9, 14))  # 3 adultes, 3 enfants, 1 bébé
        reg = logic.register_distribution(b, self.clothing, sessions=[self.s(), self.s(date(2025, 10, 30))])
        bookings = list(reg.bookings.order_by('session__date'))
        self.assertEqual(reg.tickets, 2)
        self.assertEqual((bookings[0].adults, bookings[0].children + bookings[0].babies), (2, 2))
        self.assertEqual((bookings[1].adults, bookings[1].children + bookings[1].babies), (1, 2))

    def test_capacity_in_persons(self, _):
        session = self.s()
        session.capacity = 5
        session.save()
        logic.register_distribution(make_beneficiary(adults=1, children_ages=(6, 8), name='A'),
                                    self.clothing, sessions=[session])  # 4 personnes
        self.assertEqual(session.load, 4)
        with self.assertRaises(logic.RegistrationError):
            logic.register_distribution(make_beneficiary(adults=1, name='B'), self.clothing,
                                        sessions=[session])  # 2 personnes : 6 > 5

    def test_no_waiting_period_after_attendance(self, _):
        b = make_beneficiary()
        reg = logic.register_distribution(b, self.clothing, sessions=[self.s()])
        reg.bookings.first().mark(True)
        reg2 = logic.register_distribution(b, self.clothing, sessions=[self.s(date(2025, 10, 30))])
        self.assertEqual(reg2.bookings.count(), 1)


class SimpleServiceTests(TestCase):
    def test_other_support_requires_details(self):
        other = Service.objects.get(name='Autre soutien')
        with self.assertRaises(logic.RegistrationError):
            logic.register_simple(make_beneficiary(), other, details='  ')
        reg = logic.register_simple(make_beneficiary(name='X'), other, details='Bouteille de gaz')
        self.assertEqual(reg.details, 'Bouteille de gaz')


def make_user(username, role):
    user = User.objects.create_user(username, f'{username}@example.org', 'pass1234!')
    Volunteer.objects.create(user=user, role=role)
    return user


@override_settings(EMAIL_HOST='smtp.example.org',
                   EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class FinancialAidTests(TestCase):
    def setUp(self):
        self.admin = make_user('marie', 'ADMIN')
        self.volunteer = make_user('benevole', 'VOLUNTEER_INTERVIEW')
        self.beneficiary = make_beneficiary()

    def create_via_form(self):
        form = InteractionServicesForm(
            data={'svc-aid_requested': 'on', 'svc-aid_amount': '1 200,50', 'svc-aid_nature': 'TRANSPORT',
                  'svc-aid_reason': 'Carte de bus'},
            beneficiary=self.beneficiary)
        self.assertTrue(form.is_valid(), form.errors)
        _, aid = form.save(None, self.volunteer)
        return aid

    def test_request_notifies_admins(self):
        aid = self.create_via_form()
        self.assertEqual(aid.amount, Decimal('1200.50'))
        self.assertEqual(aid.status, FinancialAidRequest.STATUS_PENDING)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('marie@example.org', mail.outbox[0].to)

    def test_reason_and_amount_required(self):
        form = InteractionServicesForm(data={'svc-aid_requested': 'on'}, beneficiary=self.beneficiary)
        self.assertFalse(form.is_valid())
        self.assertIn('aid_amount', form.errors)
        self.assertIn('aid_reason', form.errors)

    def test_rejection_requires_reason(self):
        aid = self.create_via_form()
        self.client.force_login(self.admin)
        url = reverse('services:aid_detail', args=[aid.pk])
        self.client.post(url, {'action': 'decide', 'decision': 'REJECTED', 'rejection_reason': ''})
        aid.refresh_from_db()
        self.assertEqual(aid.status, FinancialAidRequest.STATUS_PENDING)
        self.client.post(url, {'action': 'decide', 'decision': 'REJECTED', 'rejection_reason': 'Déjà aidé ce mois'})
        aid.refresh_from_db()
        self.assertEqual(aid.status, FinancialAidRequest.STATUS_REJECTED)
        self.assertEqual(aid.decided_by, self.admin)
        self.assertIn('benevole@example.org', mail.outbox[-1].to)

    def test_volunteer_cannot_decide(self):
        aid = self.create_via_form()
        self.client.force_login(self.volunteer)
        self.client.post(reverse('services:aid_detail', args=[aid.pk]), {'action': 'decide', 'decision': 'APPROVED'})
        aid.refresh_from_db()
        self.assertEqual(aid.status, FinancialAidRequest.STATUS_PENDING)

    def test_payment_by_admin(self):
        aid = self.create_via_form()
        self.client.force_login(self.admin)
        url = reverse('services:aid_detail', args=[aid.pk])
        self.client.post(url, {'action': 'decide', 'decision': 'APPROVED'})
        self.client.post(url, {'action': 'pay', 'paid_at': '24/10/2025', 'payment_method': 'CASH'})
        aid.refresh_from_db()
        self.assertEqual(aid.status, FinancialAidRequest.STATUS_PAID)
        self.assertEqual(aid.paid_at, date(2025, 10, 24))
        self.assertEqual(aid.paid_by, self.admin)

    @override_settings(EMAIL_HOST='')
    def test_no_mail_without_smtp(self):
        self.create_via_form()
        self.assertEqual(len(mail.outbox), 0)
