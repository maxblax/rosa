"""Règles métier des services : composition du foyer, sessions, inscriptions."""
from dataclasses import dataclass
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import Service, ServiceSession, ServiceRegistration, ServiceBooking

# Âge en dessous duquel un enfant est compté comme bébé dans les listes.
BABY_MAX_AGE = 3

# Horizon de recherche des sessions disponibles (en semaines).
SEARCH_WEEKS = 26


class RegistrationError(Exception):
    pass


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
    return parts


def session_dates(service, from_date=None, weeks=SEARCH_WEEKS):
    if service.session_weekday is None:
        return []
    start = from_date or timezone.localdate()
    first = start + timedelta(days=(service.session_weekday - start.weekday()) % 7)
    return [first + timedelta(weeks=i) for i in range(weeks)]


def get_or_create_session(service, day):
    session, _ = ServiceSession.objects.get_or_create(
        service=service,
        date=day,
        defaults={
            'start_time': service.session_start,
            'end_time': service.session_end,
            'capacity': service.session_capacity,
        },
    )
    return session


def upcoming_sessions(service, count=4, persons=1, from_date=None):
    """Prochaines sessions ouvertes pouvant accueillir `persons` personnes."""
    result = []
    for day in session_dates(service, from_date):
        session = get_or_create_session(service, day)
        if session.can_accept(persons):
            result.append(session)
        if len(result) >= count:
            break
    return result


def sessions_preview(service, count=4):
    """Sessions à proposer dans l'entretien, y compris complètes (affichées grisées)."""
    return [get_or_create_session(service, day) for day in session_dates(service)[:count]]


def has_pending_bookings(beneficiary, service):
    today = timezone.localdate()
    return ServiceBooking.objects.filter(
        registration__beneficiary=beneficiary,
        registration__service=service,
        registration__status=ServiceRegistration.STATUS_ACTIVE,
        session__date__gte=today,
        attended__isnull=True,
    ).exists()


@transaction.atomic
def register_distribution(beneficiary, service, user=None, interaction=None, first_session=None, details=''):
    """Inscrit une famille à un service de distribution.

    - attribution automatique : les N prochaines sessions consécutives ouvertes ;
    - date choisie : la session choisie, puis, si la famille dépasse les
      plafonds par date, les sessions suivantes pour le reste de la famille.
    """
    if not service.is_distribution:
        raise RegistrationError(f"{service.name} n'est pas un service de distribution.")
    if has_pending_bookings(beneficiary, service):
        raise RegistrationError(f"La famille a déjà une inscription en cours pour {service.name}.")

    composition = household_composition(beneficiary)
    registration = ServiceRegistration.objects.create(
        beneficiary=beneficiary, service=service, interaction=interaction,
        created_by=user, details=details,
    )

    if service.is_auto_scheduled:
        sessions = upcoming_sessions(service, count=service.sessions_per_registration,
                                     persons=composition.persons)
        if len(sessions) < service.sessions_per_registration:
            raise RegistrationError(f"Pas assez de sessions ouvertes pour {service.name}.")
        for session in sessions:
            ServiceBooking.objects.create(
                registration=registration, session=session,
                adults=composition.adults, children=composition.children, babies=composition.babies,
            )
        return registration

    parts = split_composition(service, composition)
    if first_session is None:
        raise RegistrationError(f"Choisissez une date pour {service.name}.")
    if not first_session.can_accept(parts[0].persons):
        raise RegistrationError(f"La session du {first_session.date:%d/%m/%Y} est complète.")

    used = {first_session.pk}
    ServiceBooking.objects.create(
        registration=registration, session=first_session,
        adults=parts[0].adults, children=parts[0].children, babies=parts[0].babies,
    )
    for part in parts[1:]:
        candidates = [s for s in upcoming_sessions(service, count=10, persons=part.persons,
                                                   from_date=first_session.date + timedelta(days=1))
                      if s.pk not in used]
        if not candidates:
            raise RegistrationError(f"Pas de date disponible pour répartir la famille sur {service.name}.")
        session = candidates[0]
        used.add(session.pk)
        ServiceBooking.objects.create(
            registration=registration, session=session,
            adults=part.adults, children=part.children, babies=part.babies,
        )
    return registration


def register_simple(beneficiary, service, user=None, interaction=None, details='', partner_name=''):
    if service.requires_details and not details.strip():
        raise RegistrationError(f"Précisez en toutes lettres pour « {service.name} ».")
    return ServiceRegistration.objects.create(
        beneficiary=beneficiary, service=service, interaction=interaction, created_by=user,
        details=details, partner_name=partner_name,
    )


def todays_bookings(beneficiary):
    """Réservations du jour non pointées, pour le pointage depuis la fiche."""
    return ServiceBooking.objects.filter(
        registration__beneficiary=beneficiary,
        session__date=timezone.localdate(),
        attended__isnull=True,
    ).exclude(registration__status=ServiceRegistration.STATUS_CANCELLED).select_related('session__service')
