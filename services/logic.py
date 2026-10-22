"""Règles métier des services : composition du foyer, planning, sessions, tickets."""
from dataclasses import dataclass
from datetime import time, timedelta

from django.db import transaction
from django.utils import timezone

from .models import (
    Service, ServiceScheduleSlot, ServiceSession, ServiceRegistration, ServiceBooking,
)

# Âge en dessous duquel un enfant est compté comme bébé dans les listes.
BABY_MAX_AGE = 3

# Nombre de semaines de sessions générées à l'avance à partir du planning.
HORIZON_WEEKS = 8

# Nombre de semaines proposées au bénévole pendant l'entretien.
INTERVIEW_WEEKS = 4


class RegistrationError(Exception):
    pass


def week_start(day):
    return day - timedelta(days=day.weekday())


# Composition du foyer

@dataclass
class Composition:
    adults: int
    children: int
    babies: int

    @property
    def persons(self):
        return self.adults + self.children + self.babies


def household_composition(beneficiary):
    """Composition du foyer tirée du dossier : la saisie n'est jamais refaite."""
    adults = 1 + beneficiary.household_adults.count()
    children = babies = 0
    child_records = list(beneficiary.children.all())
    if child_records:
        for child in child_records:
            age = child.age
            if age is not None and age < BABY_MAX_AGE:
                babies += 1
            else:
                children += 1
    else:
        children = beneficiary.dependents_count or 0
    return Composition(adults, children, babies)


def split_composition(service, composition):
    """Découpe une famille selon les plafonds par date du service (ex : 2 adultes et 2 enfants)."""
    max_adults = service.max_adults_per_booking
    max_kids = service.max_children_per_booking
    if not max_adults and not max_kids:
        return [composition]

    adults, children, babies = composition.adults, composition.children, composition.babies
    parts = []
    while adults or children or babies:
        take_adults = min(adults, max_adults) if max_adults else adults
        kids_room = max_kids if max_kids else children + babies
        take_babies = min(babies, kids_room)
        take_children = min(children, kids_room - take_babies)
        parts.append(Composition(take_adults, take_children, take_babies))
        adults -= take_adults
        children -= take_children
        babies -= take_babies
    return parts or [composition]


def default_tickets(service, beneficiary):
    """Passages accordés par défaut : ceux du service, ou plus si la famille doit être répartie."""
    parts = split_composition(service, household_composition(beneficiary))
    return max(service.default_tickets or 1, len(parts))


# Planning et sessions

def _previous_capacity(slot, day):
    previous = (ServiceSession.objects.filter(schedule_slot=slot, original_date__lt=day)
                .order_by('-original_date').first())
    if previous is not None:
        return previous.capacity
    if slot.capacity is not None:
        return slot.capacity
    return slot.service.session_capacity


def ensure_sessions(service, until=None):
    """Crée les sessions du planning récurrent jusqu'à `until` (par défaut : HORIZON_WEEKS)."""
    today = timezone.localdate()
    until = until or today + timedelta(weeks=HORIZON_WEEKS)
    for slot in service.schedule_slots.filter(is_active=True):
        day = today + timedelta(days=(slot.weekday - today.weekday()) % 7)
        while day <= until:
            if not ServiceSession.objects.filter(schedule_slot=slot, original_date=day).exists():
                ServiceSession.objects.create(
                    service=service, schedule_slot=slot, original_date=day, date=day,
                    start_time=slot.start_time, end_time=slot.end_time,
                    capacity=_previous_capacity(slot, day),
                )
            day += timedelta(weeks=1)


def upcoming_sessions(service, weeks=INTERVIEW_WEEKS, include_closed=False):
    ensure_sessions(service)
    today = timezone.localdate()
    qs = service.sessions.filter(date__gte=today, date__lt=week_start(today) + timedelta(weeks=weeks))
    if not include_closed:
        qs = qs.filter(is_closed=False)
    return list(qs.order_by('date', 'start_time'))


def sessions_by_week(sessions):
    """[(lundi, [sessions...]), ...] dans l'ordre chronologique."""
    weeks = {}
    for session in sessions:
        weeks.setdefault(week_start(session.date), []).append(session)
    return sorted(weeks.items())


@transaction.atomic
def save_slot(slot, previous=None):
    """Enregistre un créneau récurrent et met à jour les sessions futures non modifiées à la main.

    Les sessions qui ont déjà des réservations ne changent pas de jour : elles
    restent en place et l'admin les déplace au besoin.
    """
    slot.save()
    today = timezone.localdate()
    future = slot.sessions.filter(date__gte=today, is_customized=False)
    if previous is not None and previous.weekday != slot.weekday:
        future.filter(bookings__isnull=True).delete()
    else:
        future.update(start_time=slot.start_time, end_time=slot.end_time, capacity=slot.capacity)
    if slot.is_active:
        ensure_sessions(slot.service)
    else:
        future.filter(bookings__isnull=True).delete()


@transaction.atomic
def delete_slot(slot):
    today = timezone.localdate()
    slot.sessions.filter(date__gte=today, is_customized=False, bookings__isnull=True).delete()
    slot.is_active = False
    slot.save(update_fields=['is_active'])


def update_session(session, date=None, start_time=None, end_time=None, capacity=None, notes=None,
                   apply_to_following=False):
    """Modifie une session. La jauge peut s'appliquer aussi aux sessions suivantes du même créneau."""
    changed_schedule = (date is not None and date != session.date) or \
        start_time != session.start_time or end_time != session.end_time
    if date is not None:
        session.date = date
    session.start_time = start_time
    session.end_time = end_time
    session.capacity = capacity
    if notes is not None:
        session.notes = notes
    if changed_schedule:
        session.is_customized = True
    session.save()
    if apply_to_following and session.schedule_slot_id:
        slot = session.schedule_slot
        slot.capacity = capacity
        slot.save(update_fields=['capacity'])
        ServiceSession.objects.filter(
            schedule_slot=slot, original_date__gt=session.original_date or session.date,
        ).update(capacity=capacity)


def add_adhoc_session(service, date, start_time=None, end_time=None, capacity=None):
    if capacity is None:
        previous = service.sessions.filter(date__lte=date).order_by('-date', '-start_time').first()
        capacity = previous.capacity if previous else service.session_capacity
    return ServiceSession.objects.create(service=service, date=date, start_time=start_time,
                                         end_time=end_time, capacity=capacity, is_customized=True)


# Inscriptions et tickets

def active_registration(beneficiary, service):
    return ServiceRegistration.objects.filter(
        beneficiary=beneficiary, service=service, status=ServiceRegistration.STATUS_ACTIVE,
    ).first()


def _check_booking(registration, session, part):
    service = registration.service
    if session.service_id != service.pk:
        raise RegistrationError("Cette session n'appartient pas au service.")
    if registration.tickets_left <= 0:
        raise RegistrationError(f"Plus de passage disponible pour {service.name} : il faut un nouvel entretien.")
    if registration.bookings.filter(session=session).exists():
        raise RegistrationError(f"La famille est déjà inscrite le {session.date:%d/%m}.")
    if session.date < timezone.localdate():
        raise RegistrationError(f"La session du {session.date:%d/%m} est passée.")
    if not session.can_accept(part.persons):
        raise RegistrationError(f"La session du {session.date:%d/%m} est complète ou annulée.")
    if service.max_bookings_per_week:
        monday = week_start(session.date)
        same_week = registration.bookings.filter(
            session__date__gte=monday, session__date__lt=monday + timedelta(days=7)).count()
        if same_week >= service.max_bookings_per_week:
            raise RegistrationError(
                f"{service.name} : {service.max_bookings_per_week} passage(s) maximum par semaine "
                f"(semaine du {monday:%d/%m}).")


def book(registration, session, user=None):
    """Utilise un ticket de l'inscription sur une session."""
    parts = split_composition(registration.service, household_composition(registration.beneficiary))
    part = parts[registration.bookings.count() % len(parts)]
    _check_booking(registration, session, part)
    booking = ServiceBooking.objects.create(
        registration=registration, session=session,
        adults=part.adults, children=part.children, babies=part.babies,
    )
    registration.refresh_status()
    return booking


@transaction.atomic
def register_distribution(beneficiary, service, user=None, interaction=None, sessions=(), tickets=None,
                          details=''):
    """Inscrit une famille à un service de distribution et réserve les sessions choisies.

    Les passages non placés restent disponibles et se réservent plus tard depuis la fiche.
    """
    if not service.is_distribution:
        raise RegistrationError(f"{service.name} n'est pas un service de distribution.")
    if active_registration(beneficiary, service):
        raise RegistrationError(
            f"La famille a déjà une inscription en cours pour {service.name} : utilisez ses passages restants.")
    tickets = tickets or default_tickets(service, beneficiary)
    sessions = sorted(sessions, key=lambda s: (s.date, s.start_time or time.min))
    if len(sessions) > tickets:
        raise RegistrationError(f"{service.name} : {len(sessions)} dates choisies pour {tickets} passage(s).")

    registration = ServiceRegistration.objects.create(
        beneficiary=beneficiary, service=service, interaction=interaction,
        created_by=user, details=details, tickets=tickets,
    )
    for session in sessions:
        book(registration, session, user)
    return registration


def register_simple(beneficiary, service, user=None, interaction=None, details='', partner_name=''):
    if service.requires_details and not details.strip():
        raise RegistrationError(f"Précisez en toutes lettres pour « {service.name} ».")
    return ServiceRegistration.objects.create(
        beneficiary=beneficiary, service=service, interaction=interaction, created_by=user,
        details=details, partner_name=partner_name, tickets=1,
    )


def todays_bookings(beneficiary):
    """Réservations du jour non pointées, pour le pointage depuis la fiche."""
    return ServiceBooking.objects.filter(
        registration__beneficiary=beneficiary,
        session__date=timezone.localdate(),
        attended__isnull=True,
    ).exclude(registration__status=ServiceRegistration.STATUS_CANCELLED).select_related('session__service')
