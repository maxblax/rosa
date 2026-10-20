"""Notifications mail des demandes d'aide financière.

L'envoi n'a lieu que si un serveur SMTP est configuré (EMAIL_HOST). Sans
configuration, la notification reste visible sur le tableau de bord.
"""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Q
from django.urls import reverse

logger = logging.getLogger(__name__)


def _enabled():
    return bool(getattr(settings, 'EMAIL_HOST', ''))


def _absolute(path):
    base = getattr(settings, 'SITE_URL', '').rstrip('/')
    return f"{base}{path}" if base else path


def _send(subject, body, recipients):
    recipients = sorted({r for r in recipients if r})
    if not recipients or not _enabled():
        return False
    try:
        send_mail(f"[{settings.ASSOCIATION_NAME}] {subject}", body, None, recipients)
        return True
    except Exception:
        logger.exception("Envoi du mail impossible : %s", subject)
        return False


def admin_emails():
    User = get_user_model()
    users = User.objects.filter(is_active=True).filter(
        Q(volunteer_profile__role__in=['ADMIN', 'EMPLOYEE']) | Q(is_superuser=True)
    )
    return [u.email for u in users]


def notify_new_request(aid):
    url = _absolute(reverse('services:aid_detail', args=[aid.pk]))
    requester = aid.requested_by.get_full_name() or aid.requested_by.username if aid.requested_by else 'un bénévole'
    body = (
        f"Nouvelle demande d'aide financière à valider.\n\n"
        f"Bénéficiaire : {aid.beneficiary.full_name}\n"
        f"Montant : {aid.amount} €\n"
        f"Nature : {aid.get_nature_display()}\n"
        f"Motif : {aid.reason}\n"
        f"Demandée par : {requester}\n\n"
        f"Examiner la demande : {url}\n"
    )
    return _send("Demande d'aide financière à valider", body, admin_emails())


def notify_decision(aid):
    if not aid.requested_by or not aid.requested_by.email:
        return False
    url = _absolute(reverse('beneficiaries:detail', args=[aid.beneficiary_id]))
    body = (
        f"La demande d'aide financière de {aid.amount} € pour {aid.beneficiary.full_name} "
        f"est maintenant : {aid.get_status_display()}.\n"
    )
    if aid.rejection_reason:
        body += f"\nMotif du refus : {aid.rejection_reason}\n"
    body += f"\nFiche du bénéficiaire : {url}\n"
    return _send(f"Aide financière {aid.get_status_display().lower()}", body, [aid.requested_by.email])
