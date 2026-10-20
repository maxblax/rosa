from datetime import date, timedelta
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
from .models import Service, ServiceSession, ServiceRegistration, ServiceBooking, FinancialAidRequest

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
class GroceryTests(TestCase):
    def setUp(self):
        self.grocery = Service.objects.get(name__startswith='Épicerie')

    def test_three_consecutive_wednesdays(self, _):
        b = make_beneficiary(adults=1, children_ages=(4,))
        reg = logic.register_distribution(b, self.grocery)
        dates = [bk.session.date for bk in reg.bookings.order_by('session__date')]
        self.assertEqual(dates, [date(2025, 10, 22), date(2025, 10, 29), date(2025, 11, 5)])
        bk = reg.bookings.first()
        self.assertEqual((bk.adults, bk.children, bk.babies), (2, 1, 0))

    def test_closed_session_is_skipped(self, _):
        ServiceSession.objects.create(service=self.grocery, date=date(2025, 10, 29), is_closed=True)
        reg = logic.register_distribution(make_beneficiary(), self.grocery)
        dates = [bk.session.date for bk in reg.bookings.order_by('session__date')]
        self.assertEqual(dates, [date(2025, 10, 22), date(2025, 11, 5), date(2025, 11, 12)])

    def test_no_second_registration_while_one_is_pending(self, _):
        b = make_beneficiary()
        logic.register_distribution(b, self.grocery)
        with self.assertRaises(logic.RegistrationError):
            logic.register_distribution(b, self.grocery)

    def test_registration_done_when_all_sessions_recorded(self, _):
        reg = logic.register_distribution(make_beneficiary(), self.grocery)
        bookings = list(reg.bookings.all())
        bookings[0].mark(True)
        bookings[1].mark(False)
        reg.refresh_from_db()
        self.assertEqual(reg.status, ServiceRegistration.STATUS_ACTIVE)
        bookings[2].mark(True)
        reg.refresh_from_db()
        self.assertEqual(reg.status, ServiceRegistration.STATUS_DONE)


@mock.patch('services.logic.timezone.localdate', return_value=TODAY)
class ClothingTests(TestCase):
    def setUp(self):
        self.clothing = Service.objects.get(name__startswith='Vestiaire')

    def session(self, day=date(2025, 10, 23)):
        return logic.get_or_create_session(self.clothing, day)

    def test_small_family_single_date(self, _):
        b = make_beneficiary(adults=1, children_ages=(6,))
        reg = logic.register_distribution(b, self.clothing, first_session=self.session())
        self.assertEqual(reg.bookings.count(), 1)

    def test_large_family_split_over_two_dates(self, _):
        b = make_beneficiary(adults=2, children_ages=(2, 6, 9, 14))  # 3 adultes, 3 enfants, 1 bébé
        reg = logic.register_distribution(b, self.clothing, first_session=self.session())
        bookings = list(reg.bookings.order_by('session__date'))
        self.assertEqual(len(bookings), 2)
        self.assertEqual(bookings[0].session.date, date(2025, 10, 23))
        self.assertEqual(bookings[1].session.date, date(2025, 10, 30))
        self.assertEqual((bookings[0].adults, bookings[0].children + bookings[0].babies), (2, 2))
        self.assertEqual((bookings[1].adults, bookings[1].children + bookings[1].babies), (1, 2))

    def test_capacity_in_persons(self, _):
        session = self.session()
        session.capacity = 5
        session.save()
        logic.register_distribution(make_beneficiary(adults=1, children_ages=(6, 8), name='A'),
                                    self.clothing, first_session=session)  # 4 personnes
        self.assertEqual(session.load, 4)
        with self.assertRaises(logic.RegistrationError):
            logic.register_distribution(make_beneficiary(adults=1, name='B'), self.clothing,
                                        first_session=session)  # 2 personnes : 6 > 5

    def test_no_waiting_period_after_attendance(self, _):
        b = make_beneficiary()
        reg = logic.register_distribution(b, self.clothing, first_session=self.session())
        reg.bookings.first().mark(True)
        reg2 = logic.register_distribution(b, self.clothing, first_session=self.session(date(2025, 10, 30)))
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
