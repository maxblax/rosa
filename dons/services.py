# -*- coding: utf-8 -*-
"""
Service pour l integration avec l API HelloAsso
"""
import requests
from datetime import datetime, timedelta
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class HelloAssoService:
    """Service pour interagir avec l API HelloAsso"""

    BASE_URL = "https://api.helloasso.com/v5"
    OAUTH_URL = "https://api.helloasso.com/oauth2/token"

    def __init__(self):
        self.client_id = settings.HELLOASSO_API_KEY
        self.client_secret = settings.HELLOASSO_API_SECRET
        self.organization_slug = settings.HELLOASSO_ORGANIZATION_SLUG
        self.access_token = None
        self.token_expires_at = None

    def is_enabled(self):
        """Verifie si l integration HelloAsso est activee et configuree"""
        return (
            settings.ENABLE_HELLOASSO_INTEGRATION
            and self.client_id
            and self.client_secret
            and self.organization_slug
        )

    def authenticate(self):
        """Obtient un token OAuth2 depuis HelloAsso"""
        if not self.is_enabled():
            logger.warning("HelloAsso integration is not enabled or not configured")
            return False

        # Si on a deja un token valide, pas besoin de re-authentifier
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return True

        try:
            response = requests.post(
                self.OAUTH_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )
            response.raise_for_status()

            data = response.json()
            self.access_token = data.get("access_token")
            expires_in = data.get("expires_in", 1800)  # Default 30 minutes

            # On retire 5 minutes pour avoir une marge de securite
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)

            logger.info("Successfully authenticated with HelloAsso API")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to authenticate with HelloAsso API: {e}")
            return False

    def get_donations(self, from_date=None, to_date=None, page_size=100):
        """
        Recupere les dons depuis HelloAsso

        Args:
            from_date: Date de debut (datetime ou None)
            to_date: Date de fin (datetime ou None)
            page_size: Nombre de resultats par page

        Returns:
            Liste de dictionnaires representant les dons
        """
        if not self.is_enabled():
            logger.warning("HelloAsso integration is not enabled")
            return []

        if not self.authenticate():
            logger.error("Failed to authenticate with HelloAsso")
            return []

        donations = []
        page_index = 1
        continuation_token = None

        try:
            while True:
                # Construire les parametres de la requete
                params = {
                    "pageSize": page_size,
                    "pageIndex": page_index,
                    "states": "Authorized",  # Seulement les paiements valides
                    "sortOrder": "Desc",
                    "sortField": "Date",
                }

                if from_date:
                    params["from"] = from_date.isoformat()
                if to_date:
                    params["to"] = to_date.isoformat()
                if continuation_token:
                    params["continuationToken"] = continuation_token

                # Requete a l API
                endpoint = f"{self.BASE_URL}/organizations/{self.organization_slug}/payments"
                response = requests.get(
                    endpoint,
                    params=params,
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=10,
                )
                response.raise_for_status()

                data = response.json()

                # Extraire les donnees de paiement
                payments = data.get("data", [])
                if not payments:
                    break

                # Transformer les paiements en dons normalises
                for payment in payments:
                    donation = self._normalize_payment(payment)
                    if donation:
                        donations.append(donation)

                # Gerer la pagination
                pagination = data.get("pagination", {})
                continuation_token = pagination.get("continuationToken")

                # Si pas de token de continuation, on a tout recupere
                if not continuation_token:
                    break

                page_index += 1

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch donations from HelloAsso: {e}")

        return donations

    def _normalize_payment(self, payment):
        """
        Normalise un paiement HelloAsso en format compatible avec notre application

        Args:
            payment: Dictionnaire representant un paiement HelloAsso

        Returns:
            Dictionnaire normalise ou None
        """
        try:
            # Extraire les informations du payeur
            payer = payment.get("payer", {})
            payer_name = None

            if payer:
                first_name = payer.get("firstName", "")
                last_name = payer.get("lastName", "")
                if first_name or last_name:
                    payer_name = f"{first_name} {last_name}".strip()

            # Determiner si c est anonyme
            is_anonymous = not bool(payer_name)

            # Extraire la date (peut etre sous differents formats)
            date_str = payment.get("date") or payment.get("creationDate")
            date_obj = None
            if date_str:
                try:
                    date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except ValueError:
                    logger.warning(f"Could not parse date: {date_str}")

            # Creer le don normalise
            return {
                "id": payment.get("id"),
                "donor_name": payer_name if not is_anonymous else None,
                "amount": payment.get("amount", 0) / 100,  # Montant en centimes -> euros
                "date": date_obj.date() if date_obj else None,
                "datetime": date_obj,
                "is_anonymous": is_anonymous,
                "payment_type": "TRANSFER",  # Par defaut, HelloAsso = virement
                "source": "HelloAsso",
                "notes": f"Don via HelloAsso (ID: {payment.get('id')})",
            }

        except Exception as e:
            logger.error(f"Failed to normalize payment: {e}")
            return None


# Instance singleton du service
helloasso_service = HelloAssoService()
