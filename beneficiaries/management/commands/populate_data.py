"""
Commande Django pour populer la base de données avec des données de démonstration réalistes.

Cette commande génère:
- Des utilisateurs avec différents rôles (admin, salariés, bénévoles entretien, gouvernance)
- Des bénéficiaires avec des profils variés
- Des snapshots financiers avec données partielles sur plusieurs mois
- Des créneaux de disponibilité et rendez-vous
- Des interactions et suivis

Usage: python manage.py populate_data [--clear]
"""

import random
from datetime import datetime, date, timedelta, time
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from faker import Faker

from beneficiaries.models import Beneficiary, FinancialSnapshot, Child, Interaction
from volunteers.models import Volunteer
from calendar_app.models import VolunteerCalendar, AvailabilitySlot, Appointment
from partners.models import Partner
from news.models import News

fake = Faker('fr_FR')


class Command(BaseCommand):
    help = 'Peuple la base de données avec des données de démonstration réalistes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Efface toutes les données existantes avant de créer les nouvelles',
        )
        parser.add_argument(
            '--users',
            type=int,
            default=12,
            help='Nombre d\'utilisateurs à créer (défaut: 12)',
        )
        parser.add_argument(
            '--beneficiaries',
            type=int,
            default=15,
            help='Nombre de bénéficiaires à créer (défaut: 15)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Début de la population des données de démonstration')
        )

        if options['clear']:
            self.clear_data()

        with transaction.atomic():
            # Créer les utilisateurs et profils de bénévoles
            users = self.create_users(options['users'])
            self.stdout.write(
                self.style.SUCCESS(f'✅ {len(users)} utilisateurs créés')
            )

            # Créer les bénéficiaires
            beneficiaries = self.create_beneficiaries(options['beneficiaries'])
            self.stdout.write(
                self.style.SUCCESS(f'✅ {len(beneficiaries)} bénéficiaires créés')
            )

            # Créer les snapshots financiers
            snapshots_count = self.create_financial_snapshots(beneficiaries)
            self.stdout.write(
                self.style.SUCCESS(f'✅ {snapshots_count} snapshots financiers créés')
            )

            # Créer les créneaux de disponibilité et rendez-vous
            appointments_count = self.create_calendar_data(users)
            self.stdout.write(
                self.style.SUCCESS(f'✅ {appointments_count} rendez-vous créés')
            )

            # Créer les interactions
            interactions_count = self.create_interactions(beneficiaries, users)
            self.stdout.write(
                self.style.SUCCESS(f'✅ {interactions_count} interactions créées')
            )

            # Créer les partenaires
            partners_count = self.create_partners()
            self.stdout.write(
                self.style.SUCCESS(f'✅ {partners_count} partenaires créés')
            )

            # Créer les actualités
            news_count = self.create_news()
            self.stdout.write(
                self.style.SUCCESS(f'✅ {news_count} actualités créées')
            )

        self.stdout.write(
            self.style.SUCCESS('🎉 Population des données terminée avec succès!')
        )

    def clear_data(self):
        """Efface toutes les données existantes"""
        self.stdout.write('🧹 Nettoyage des données existantes...')

        # Supprimer dans l'ordre pour éviter les contraintes de clés étrangères
        Appointment.objects.all().delete()
        AvailabilitySlot.objects.all().delete()
        VolunteerCalendar.objects.all().delete()
        Interaction.objects.all().delete()
        Child.objects.all().delete()
        FinancialSnapshot.objects.all().delete()
        Beneficiary.objects.all().delete()
        Partner.objects.all().delete()
        News.objects.all().delete()
        Volunteer.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write(self.style.WARNING('⚠️  Données existantes supprimées'))

    def create_users(self, count):
        """Crée des utilisateurs avec différents rôles"""
        users = []

        # Définir la répartition des rôles
        roles_distribution = [
            ('ADMIN', 1),
            ('EMPLOYEE', 2),
            ('VOLUNTEER_INTERVIEW', count - 4),
            ('VOLUNTEER_GOVERNANCE', 1),
        ]

        for role, role_count in roles_distribution:
            for i in range(role_count):
                # Générer un utilisateur
                first_name = fake.first_name()
                last_name = fake.last_name().upper()  # Nom de famille en majuscules
                username = f"{first_name.lower()}.{last_name.lower()}"
                email = f"{username}@ona-demo.fr"

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password='demo123',  # Mot de passe simple pour la démo
                )

                # Créer le profil de bénévole associé
                volunteer = Volunteer.objects.create(
                    user=user,
                    civility=random.choice(['M', 'MME']),
                    birth_date=fake.date_of_birth(minimum_age=25, maximum_age=70),
                    phone=fake.phone_number(),
                    address=fake.address(),
                    role=role,
                    skills=self.generate_skills(),
                    join_date=fake.date_between(start_date='-2y', end_date='today'),
                )

                users.append(user)

        return users

    def generate_skills(self):
        """Génère des compétences réalistes pour un bénévole"""
        skills_pool = [
            "Accompagnement social", "Aide administrative", "Informatique",
            "Traduction (anglais, arabe, espagnol)", "Comptabilité",
            "Juridique", "Santé", "Éducation", "Cuisine", "Mécanique",
            "Jardinage", "Couture", "Formation", "Animation"
        ]
        return ", ".join(random.sample(skills_pool, random.randint(2, 4)))


    def create_beneficiaries(self, count):
        """Crée des bénéficiaires avec des profils diversifiés"""
        beneficiaries = []

        for i in range(count):
            civility = random.choice(['M', 'MME'])
            first_name = fake.first_name_male() if civility == 'M' else fake.first_name_female()
            last_name = fake.last_name().upper()

            beneficiary = Beneficiary.objects.create(
                civility=civility,
                first_name=first_name,
                last_name=last_name,
                birth_date=fake.date_of_birth(minimum_age=18, maximum_age=80),
                phone=fake.phone_number() if random.choice([True, False]) else '',
                email=fake.email() if random.choice([True, False]) else '',
                address=fake.address(),
                residence_address=fake.address() if random.choice([True, False]) else '',
                occupation=fake.job() if random.choice([True, False]) else '',
                housing_status=random.choice([
                    'CADA', 'CAO', 'CHRS', 'DIFFUS', 'COLLECTIF', 'QPV', 'AUTRE'
                ]),
                family_status=random.choice([
                    'CELIBATAIRE', 'MARIE', 'VEUF', 'VIE_MARITALE', 'DIVORCE', 'SEPARE'
                ]),
                dependents_count=random.randint(0, 4),
            )

            # Créer des enfants pour certains bénéficiaires
            if beneficiary.dependents_count > 0:
                self.create_children(beneficiary)

            beneficiaries.append(beneficiary)

        return beneficiaries

    def create_children(self, beneficiary):
        """Crée des enfants pour un bénéficiaire"""
        for i in range(beneficiary.dependents_count):
            Child.objects.create(
                beneficiary=beneficiary,
                first_name=fake.first_name(),
                last_name=beneficiary.last_name,
                birth_date=fake.date_of_birth(minimum_age=0, maximum_age=18),
                observations=fake.sentence() if random.choice([True, False]) else '',
            )

    def create_financial_snapshots(self, beneficiaries):
        """Crée des snapshots financiers avec données partielles"""
        snapshots_count = 0

        for beneficiary in beneficiaries:
            # Créer entre 1 et 6 mois d'historique
            months_back = random.randint(1, 6)

            for i in range(months_back):
                # Date du snapshot (premier jour du mois)
                snapshot_date = timezone.now() - timedelta(days=30*i)
                snapshot_date = snapshot_date.replace(day=1, hour=10, minute=0, second=0)

                snapshot = FinancialSnapshot.objects.create(
                    beneficiary=beneficiary,
                    date=snapshot_date,
                    **self.generate_financial_data()
                )
                snapshots_count += 1

        return snapshots_count

    def generate_financial_data(self):
        """Génère des données financières réalistes avec des données partielles"""
        data = {}

        # Prestations sociales (certaines remplies, d'autres vides)
        if random.choice([True, False]):
            data['rsa_prime_activite'] = Decimal(str(random.uniform(400, 600)))

        if random.choice([True, False]):
            data['aah_pension_invalidite'] = Decimal(str(random.uniform(800, 900)))

        if random.choice([True, False]):
            data['apl'] = Decimal(str(random.uniform(150, 300)))

        if random.choice([True, False]):
            data['af'] = Decimal(str(random.uniform(100, 250)))

        if random.choice([True, False]):
            data['paje'] = Decimal(str(random.uniform(50, 180)))

        # Revenus du travail (plus rares)
        if random.random() < 0.3:  # 30% de chances
            data['salaire'] = Decimal(str(random.uniform(800, 1500)))

        if random.random() < 0.2:  # 20% de chances
            data['france_travail'] = Decimal(str(random.uniform(600, 1200)))

        # ADA pour certains (demandeurs d'asile)
        if random.random() < 0.15:  # 15% de chances
            data['ada'] = Decimal(str(random.uniform(200, 400)))

        # Charges (certaines toujours présentes, d'autres optionnelles)
        if random.choice([True, False]):
            data['loyer_residuel'] = Decimal(str(random.uniform(200, 500)))

        if random.choice([True, False]):
            data['energie'] = Decimal(str(random.uniform(50, 150)))

        if random.choice([True, False]):
            data['transport_commun'] = Decimal(str(random.uniform(30, 80)))

        if random.choice([True, False]):
            data['frais_scolaires'] = Decimal(str(random.uniform(20, 100)))

        # Dettes (occasionnelles)
        if random.random() < 0.3:
            data['credit_consommation'] = Decimal(str(random.uniform(100, 300)))

        if random.random() < 0.2:
            data['dettes_diverses'] = Decimal(str(random.uniform(50, 200)))

        return data

    def create_calendar_data(self, users):
        """Crée des créneaux de disponibilité et des rendez-vous"""
        appointments_count = 0

        # Filtrer les utilisateurs qui peuvent avoir des calendriers
        eligible_users = [
            user for user in users
            if hasattr(user, 'volunteer_profile') and
            user.volunteer_profile.role != 'VOLUNTEER_GOVERNANCE'
        ]

        for user in eligible_users:
            volunteer = user.volunteer_profile

            # Le calendrier est créé automatiquement par le signal
            calendar = volunteer.calendar

            # Créer des créneaux de disponibilité
            self.create_availability_slots(calendar)

            # Créer des rendez-vous avec répartition inégale
            if volunteer.role == 'VOLUNTEER_INTERVIEW':
                # Certains bénévoles ont beaucoup de RDV, d'autres peu
                appointments_for_volunteer = random.choices(
                    [2, 5, 8, 12, 15],
                    weights=[30, 25, 20, 15, 10]  # Répartition inégale
                )[0]
            else:
                appointments_for_volunteer = random.randint(3, 8)

            appointments_count += self.create_appointments(calendar, appointments_for_volunteer)

        return appointments_count

    def create_availability_slots(self, calendar):
        """Crée des créneaux de disponibilité pour un calendrier"""
        volunteer = calendar.volunteer

        # Créer 2-4 créneaux récurrents par bénévole
        num_slots = random.randint(2, 4)

        for i in range(num_slots):
            weekday = random.randint(0, 4)  # Lundi à vendredi principalement
            start_hour = random.choice([8, 9, 10, 14, 15, 16])
            duration = random.choice([2, 3, 4])  # 2-4h de créneaux

            AvailabilitySlot.objects.create(
                volunteer_calendar=calendar,
                slot_type='AVAILABILITY',
                recurrence_type='WEEKLY',
                weekday=weekday,
                start_time=time(start_hour, 0),
                end_time=time(start_hour + duration, 0),
                valid_from=date.today() - timedelta(days=30),
                valid_until=date.today() + timedelta(days=90),
                title=f"Disponibilité {['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi'][weekday]}",
                is_bookable=True,
                max_appointments=random.choice([1, 2, 3]),
                created_by=volunteer.user,
            )

    def create_appointments(self, calendar, count):
        """Crée des rendez-vous pour un calendrier"""
        beneficiaries = list(Beneficiary.objects.all())
        appointments_created = 0

        for i in range(count):
            # Répartir les RDV entre passé, présent et futur
            if i < count * 0.6:  # 60% dans le passé
                appointment_date = fake.date_between(
                    start_date='-30d',
                    end_date='-1d'
                )
                status = random.choice(['COMPLETED', 'CANCELLED', 'NO_SHOW'])
            elif i < count * 0.8:  # 20% dans les prochains jours
                appointment_date = fake.date_between(
                    start_date='today',
                    end_date='+7d'
                )
                status = random.choice(['SCHEDULED', 'CONFIRMED'])
            else:  # 20% dans le futur
                appointment_date = fake.date_between(
                    start_date='+8d',
                    end_date='+60d'
                )
                status = 'SCHEDULED'

            start_hour = random.choice([9, 10, 11, 14, 15, 16])
            duration = random.choice([1, 1.5, 2])
            end_hour = start_hour + duration

            beneficiary = random.choice(beneficiaries)

            appointment = Appointment.objects.create(
                volunteer_calendar=calendar,
                beneficiary=beneficiary,
                appointment_date=appointment_date,
                start_time=time(int(start_hour), int((start_hour % 1) * 60)),
                end_time=time(int(end_hour), int((end_hour % 1) * 60)),
                appointment_type=random.choice([
                    'INTERVIEW', 'FOLLOW_UP', 'ADMINISTRATIVE', 'SOCIAL'
                ]),
                title=self.generate_appointment_title(),
                description=fake.sentence(nb_words=10),
                location="Association ONA" if random.choice([True, False]) else fake.address(),
                status=status,
                preparation_notes=fake.sentence() if random.choice([True, False]) else '',
                completion_notes=fake.paragraph() if status == 'COMPLETED' else '',
                created_by=calendar.volunteer.user,
            )
            appointments_created += 1

        return appointments_created

    def generate_appointment_title(self):
        """Génère des titres réalistes pour les rendez-vous"""
        titles = [
            "Premier entretien", "Suivi mensuel", "Aide administrative",
            "Renouvellement dossier", "Accompagnement social",
            "Point situation", "Aide démarches", "Entretien de suivi",
            "Évaluation besoins", "Orientation services"
        ]
        return random.choice(titles)

    def create_interactions(self, beneficiaries, users):
        """Crée des interactions entre bénévoles et bénéficiaires"""
        interactions_count = 0

        # Filtrer les utilisateurs qui peuvent créer des interactions
        eligible_users = [
            user for user in users
            if hasattr(user, 'volunteer_profile') and
            user.volunteer_profile.role in ['VOLUNTEER_INTERVIEW', 'EMPLOYEE', 'ADMIN']
        ]

        for beneficiary in beneficiaries:
            # Chaque bénéficiaire a entre 2 et 8 interactions
            num_interactions = random.randint(2, 8)

            for i in range(num_interactions):
                user = random.choice(eligible_users)

                # Date d'interaction (répartie sur plusieurs mois)
                interaction_date = fake.date_time_between(
                    start_date='-6M',
                    end_date='now'
                )

                interaction = Interaction.objects.create(
                    beneficiary=beneficiary,
                    user=user,
                    interaction_type=random.choice([
                        'ASSOCIATION', 'EXTERNAL', 'PHONE', 'HOME_VISIT', 'EMAIL'
                    ]),
                    title=self.generate_interaction_title(),
                    description=fake.paragraph(nb_sentences=3),
                    changes_made=fake.sentence() if random.choice([True, False]) else '',
                    follow_up_required=random.choice([True, False]),
                    follow_up_date=fake.date_between(
                        start_date='today',
                        end_date='+30d'
                    ) if random.choice([True, False]) else None,
                    follow_up_notes=fake.sentence() if random.choice([True, False]) else '',
                    created_at=interaction_date,
                )
                interactions_count += 1

        return interactions_count

    def generate_interaction_title(self):
        """Génère des titres réalistes pour les interactions"""
        titles = [
            "Entretien d'accueil", "Suivi situation financière",
            "Aide constitution dossier", "Orientation vers partenaires",
            "Accompagnement démarches", "Évaluation besoins",
            "Point situation logement", "Aide administrative",
            "Entretien téléphonique", "Visite de suivi"
        ]
        return random.choice(titles)

    def create_partners(self):
        """Crée des partenaires avec des services variés"""
        partners_data = [
            {
                'name': 'Banque Alimentaire',
                'address': '123 Rue de la Solidarité, 75001 Paris',
                'phone': '01 23 45 67 89',
                'email': 'contact@banquealimentaire.org',
                'services': 'Distribution alimentaire, Collecte de dons'
            },
            {
                'name': 'Croix Rouge',
                'address': '456 Avenue de l\'Entraide, 75002 Paris',
                'phone': '01 98 76 54 32',
                'email': 'contact@croixrouge.org',
                'services': 'Vestiaire social, Aide médicale, Formation premiers secours'
            },
            {
                'name': 'Restos du Cœur',
                'address': '789 Boulevard du Partage, 75003 Paris',
                'phone': '01 45 67 89 12',
                'email': 'contact@restosducoeur.org',
                'services': 'Repas chauds, Aide alimentaire, Accompagnement social'
            },
            {
                'name': 'Secours Populaire',
                'address': '321 Rue de l\'Entraide, 75010 Paris',
                'phone': '01 44 78 21 00',
                'email': 'contact@secourspopulaire.fr',
                'services': 'Aide alimentaire, Vestiaire, Aide aux devoirs, Vacances enfants'
            },
            {
                'name': 'Emmaüs',
                'address': '654 Avenue de la Fraternité, 75011 Paris',
                'phone': '01 41 58 25 00',
                'email': 'contact@emmaus.org',
                'services': 'Hébergement d\'urgence, Insertion professionnelle, Collecte de dons'
            },
            {
                'name': 'Médecins du Monde',
                'address': '987 Rue de la Santé, 75013 Paris',
                'phone': '01 44 92 15 15',
                'email': 'contact@medecinsdumonde.org',
                'services': 'Soins médicaux gratuits, Accompagnement social, Orientation santé'
            },
            {
                'name': 'France Horizon',
                'address': '147 Boulevard de l\'Avenir, 75014 Paris',
                'phone': '01 53 27 64 00',
                'email': 'contact@francehorizon.fr',
                'services': 'Accompagnement emploi, Formation professionnelle, Coaching'
            },
            {
                'name': 'Habitat et Humanisme',
                'address': '258 Rue du Logement, 75015 Paris',
                'phone': '01 42 11 20 00',
                'email': 'contact@habitat-humanisme.org',
                'services': 'Aide au logement, Accompagnement logement, Intermédiation locative'
            },
        ]

        partners_count = 0
        for partner_data in partners_data:
            Partner.objects.create(**partner_data)
            partners_count += 1

        return partners_count

    def create_news(self):
        """Crée des actualités avec différents types"""
        news_data = [
            {
                'title': 'Distribution alimentaire exceptionnelle ce weekend',
                'news_type': 'EVENEMENT',
                'description': 'Nous organisons une distribution alimentaire exceptionnelle samedi de 9h à 12h. Inscription nécessaire auprès de l\'accueil.',
                'is_pinned': True,
            },
            {
                'title': 'Nouveau partenariat avec la banque alimentaire',
                'news_type': 'PARTENARIAT',
                'description': 'Grâce à notre nouveau partenariat avec la banque alimentaire locale, nous pourrons désormais proposer une plus grande variété de produits frais.',
                'is_pinned': False,
            },
            {
                'title': 'Formation des bénévoles le mois prochain',
                'news_type': 'FORMATION',
                'description': 'Une session de formation pour les nouveaux bénévoles aura lieu le premier samedi du mois prochain. Inscription obligatoire.',
                'is_pinned': False,
            },
            {
                'title': 'Permanence administrative tous les mercredis',
                'news_type': 'INFO',
                'description': 'À partir de ce mois-ci, nous proposons une permanence dédiée aux démarches administratives tous les mercredis après-midi sur rendez-vous.',
                'is_pinned': False,
            },
            {
                'title': 'Collecte de vêtements d\'hiver',
                'news_type': 'EVENEMENT',
                'description': 'Nous lançons une grande collecte de vêtements chauds pour l\'hiver. Vous pouvez déposer vos dons à l\'accueil du lundi au vendredi.',
                'is_pinned': False,
            },
        ]

        news_count = 0
        for i, news_item_data in enumerate(news_data):
            # Échelonner les dates de publication (du plus récent au plus ancien)
            publication_offset = timedelta(days=i * 2)
            news_item = News(**news_item_data)
            news_item.save()
            # Modifier la date de publication après création
            news_item.publication_date = (date.today() - publication_offset)
            news_item.save()
            news_count += 1

        return news_count