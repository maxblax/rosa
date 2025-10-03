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
from analysis.models import ChartConfig

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

            # Créer les graphiques d'analyse
            charts_count = self.create_analysis_charts()
            self.stdout.write(
                self.style.SUCCESS(f'✅ {charts_count} graphiques d\'analyse créés')
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
        ChartConfig.objects.all().delete()
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

    def create_analysis_charts(self):
        """Crée des graphiques d'analyse de démonstration"""
        charts_data = [
            # IMPACT SOCIAL
            {
                'title': 'Nombre de personnes touchées',
                'section': 'IMPACT',
                'chart_type': 'bar',
                'size': 'half',
                'display_order': 1,
                'y_axis_label': 'Nombre de personnes',
                'description': 'Total bénéficiaires + enfants',
                'query_code': '''
beneficiaries_count = Beneficiary.objects.count()
children_count = Child.objects.count()
result = {
    'labels': ['Bénéficiaires', 'Enfants', 'Total'],
    'datasets': [{
        'label': 'Personnes touchées',
        'data': [beneficiaries_count, children_count, beneficiaries_count + children_count],
        'backgroundColor': ['#3b82f6', '#10b981', '#8b5cf6']
    }]
}
'''
            },
            # DEMOGRAPHIC
            {
                'title': 'Répartition par statut de logement',
                'section': 'DEMOGRAPHIC',
                'chart_type': 'bar',
                'size': 'full',
                'display_order': 2,
                'y_axis_label': 'Nombre de bénéficiaires',
                'description': 'Distribution des bénéficiaires par type d\'hébergement',
                'query_code': '''
from django.db.models import Count
stats = Beneficiary.objects.values('housing_status').annotate(count=Count('id')).order_by('-count')
labels = [item['housing_status'] or 'Non renseigné' for item in stats]
data = [item['count'] for item in stats]
result = {
    'labels': labels,
    'datasets': [{
        'label': 'Bénéficiaires',
        'data': data,
        'backgroundColor': '#3b82f6'
    }]
}
'''
            },
            # FINANCIAL - Reste à vivre par nombre d'enfants
            {
                'title': 'Évolution du Reste à Vivre par Bénéficiaire',
                'section': 'FINANCIAL',
                'chart_type': 'bar',
                'size': 'full',
                'display_order': 3,
                'y_axis_label': 'Reste à vivre moyen (€)',
                'x_axis_label': 'Mois',
                'description': 'Reste à vivre selon le nombre d\'enfants (revenus - charges)',
                'query_code': '''
today = datetime.now().date()
labels = []
data_0_enfants = []
data_1_2_enfants = []
data_3plus_enfants = []

for i in range(5, -1, -1):
    month_date = today - timedelta(days=30*i)
    labels.append(month_date.strftime('%b'))

    # Snapshots du mois
    snapshots = FinancialSnapshot.objects.filter(
        date__year=month_date.year,
        date__month=month_date.month
    ).select_related('beneficiary')

    # Grouper par nombre d'enfants
    rav_0 = []
    rav_1_2 = []
    rav_3plus = []

    for snap in snapshots:
        # Calcul revenus
        revenus = (snap.rsa_prime_activite or 0) + (snap.salaire or 0) + (snap.france_travail or 0) + (snap.aah_pension_invalidite or 0) + (snap.retraite_aspa or 0) + (snap.ada or 0) + (snap.paje or 0) + (snap.af or 0) + (snap.cf or 0) + (snap.asf or 0) + (snap.pension_alimentaire or 0) + (snap.autres_revenus or 0)

        # Calcul charges
        charges = (snap.loyer_residuel or 0) + (snap.energie or 0) + (snap.eau or 0) + (snap.transport_commun or 0) + (snap.carburant or 0) + (snap.credit_consommation or 0) + (snap.mutuelle_privee or 0) + (snap.frais_sante_non_rembourses or 0) + (snap.frais_scolaires or 0) + (snap.dettes_diverses or 0)

        reste_a_vivre = revenus - charges

        # Grouper selon nombre d'enfants
        nb_enfants = snap.beneficiary.dependents_count
        if nb_enfants == 0:
            rav_0.append(reste_a_vivre)
        elif nb_enfants <= 2:
            rav_1_2.append(reste_a_vivre)
        else:
            rav_3plus.append(reste_a_vivre)

    data_0_enfants.append(sum(rav_0) / len(rav_0) if rav_0 else 0)
    data_1_2_enfants.append(sum(rav_1_2) / len(rav_1_2) if rav_1_2 else 0)
    data_3plus_enfants.append(sum(rav_3plus) / len(rav_3plus) if rav_3plus else 0)

result = {
    'labels': labels,
    'datasets': [
        {
            'label': '0 enfants',
            'data': data_0_enfants,
            'backgroundColor': '#8b5cf6'
        },
        {
            'label': '1-2 enfants',
            'data': data_1_2_enfants,
            'backgroundColor': '#10b981'
        },
        {
            'label': '3+ enfants',
            'data': data_3plus_enfants,
            'backgroundColor': '#f59e0b'
        }
    ]
}
'''
            },
            # OPERATIONAL
            {
                'title': 'Volume d\'interactions mensuelles',
                'section': 'OPERATIONAL',
                'chart_type': 'bar',
                'size': 'full',
                'display_order': 4,
                'y_axis_label': 'Nombre d\'interactions',
                'x_axis_label': 'Mois',
                'description': 'Nombre total d\'interactions par mois sur 6 mois',
                'query_code': '''
today = datetime.now().date()
labels = []
data = []
for i in range(5, -1, -1):
    month_date = today - timedelta(days=30*i)
    labels.append(month_date.strftime('%b %Y'))
    count = Interaction.objects.filter(
        created_at__year=month_date.year,
        created_at__month=month_date.month
    ).count()
    data.append(count)
result = {
    'labels': labels,
    'datasets': [{
        'label': 'Interactions',
        'data': data,
        'backgroundColor': '#3b82f6'
    }]
}
'''
            },
            # TRENDS
            {
                'title': 'Évolution du nombre de bénéficiaires',
                'section': 'TRENDS',
                'chart_type': 'line',
                'size': 'full',
                'display_order': 5,
                'y_axis_label': 'Nombre de bénéficiaires',
                'x_axis_label': 'Mois',
                'description': 'Croissance du nombre total de bénéficiaires sur 12 mois',
                'query_code': '''
today = datetime.now().date()
labels = []
data = []
for i in range(11, -1, -1):
    month_date = today - timedelta(days=30*i)
    month_end = month_date.replace(day=28)  # Approximation
    labels.append(month_date.strftime('%b %Y'))
    count = Beneficiary.objects.filter(created_at__lte=month_end).count()
    data.append(count)
result = {
    'labels': labels,
    'datasets': [{
        'label': 'Bénéficiaires',
        'data': data,
        'borderColor': '#8b5cf6',
        'backgroundColor': 'rgba(139, 92, 246, 0.1)',
        'tension': 0.3,
        'fill': True
    }]
}
'''
            },
            # OPERATIONAL
            {
                'title': 'Répartition des types d\'interaction',
                'section': 'OPERATIONAL',
                'chart_type': 'bar',
                'size': 'full',
                'display_order': 6,
                'y_axis_label': 'Nombre d\'interactions',
                'description': 'Distribution des interactions par type',
                'query_code': '''
from django.db.models import Count
stats = Interaction.objects.values('interaction_type').annotate(count=Count('id')).order_by('-count')
labels = [item['interaction_type'] for item in stats]
data = [item['count'] for item in stats]
result = {
    'labels': labels,
    'datasets': [{
        'label': 'Interactions',
        'data': data,
        'backgroundColor': '#3b82f6'
    }]
}
'''
            },
            # IMPACT - Snapshots financiers créés
            {
                'title': 'Photos financières créées par mois',
                'section': 'IMPACT',
                'chart_type': 'bar',
                'size': 'half',
                'display_order': 7,
                'y_axis_label': 'Nombre de snapshots',
                'description': 'Suivi mensuel des situations financières',
                'query_code': '''
today = datetime.now().date()
labels = []
data = []
for i in range(5, -1, -1):
    month_date = today - timedelta(days=30*i)
    labels.append(month_date.strftime('%b %Y'))
    # Compter les snapshots financiers créés ce mois
    count = FinancialSnapshot.objects.filter(
        date__year=month_date.year,
        date__month=month_date.month
    ).count()
    data.append(count)
result = {
    'labels': labels,
    'datasets': [{
        'label': 'Snapshots financiers',
        'data': data,
        'backgroundColor': '#10b981'
    }]
}
'''
            },
            # DEMOGRAPHIC - Distribution par âge
            {
                'title': 'Distribution des bénéficiaires par tranche d\'âge',
                'section': 'DEMOGRAPHIC',
                'chart_type': 'bar',
                'size': 'full',
                'display_order': 8,
                'y_axis_label': 'Nombre de bénéficiaires',
                'x_axis_label': 'Tranche d\'âge',
                'description': 'Répartition démographique par groupes d\'âge',
                'query_code': '''
today = datetime.now().date()
age_groups = {'0-17': 0, '18-25': 0, '26-40': 0, '41-60': 0, '61+': 0, 'Non renseigné': 0}
for ben in Beneficiary.objects.all():
    if ben.birth_date:
        age = (today - ben.birth_date).days // 365
        if age < 18:
            age_groups['0-17'] += 1
        elif age < 26:
            age_groups['18-25'] += 1
        elif age < 41:
            age_groups['26-40'] += 1
        elif age < 61:
            age_groups['41-60'] += 1
        else:
            age_groups['61+'] += 1
    else:
        age_groups['Non renseigné'] += 1
result = {
    'labels': list(age_groups.keys()),
    'datasets': [{
        'label': 'Bénéficiaires',
        'data': list(age_groups.values()),
        'backgroundColor': '#3b82f6'
    }]
}
'''
            },
            # DEMOGRAPHIC - Situation familiale
            {
                'title': 'Situation familiale des bénéficiaires',
                'section': 'DEMOGRAPHIC',
                'chart_type': 'bar',
                'size': 'full',
                'display_order': 9,
                'y_axis_label': 'Nombre de bénéficiaires',
                'description': 'Répartition par situation familiale',
                'query_code': '''
from django.db.models import Count
stats = Beneficiary.objects.values('family_status').annotate(count=Count('id')).order_by('-count')
labels = []
for item in stats:
    fs = item['family_status']
    if fs == 'CELIBATAIRE':
        labels.append('Célibataire')
    elif fs == 'MARIE':
        labels.append('Marié(e)')
    elif fs == 'DIVORCE':
        labels.append('Divorcé(e)')
    elif fs == 'VEUF':
        labels.append('Veuf(ve)')
    elif fs == 'VIE_MARITALE':
        labels.append('Vie maritale')
    elif fs == 'SEPARE':
        labels.append('Séparé(e)')
    else:
        labels.append('Autre')
data = [item['count'] for item in stats]
result = {
    'labels': labels,
    'datasets': [{
        'label': 'Bénéficiaires',
        'data': data,
        'backgroundColor': '#10b981'
    }]
}
'''
            },
            # DEMOGRAPHIC - Nombre d'enfants à charge
            {
                'title': 'Répartition par nombre d\'enfants à charge',
                'section': 'DEMOGRAPHIC',
                'chart_type': 'bar',
                'size': 'half',
                'display_order': 10,
                'y_axis_label': 'Nombre de bénéficiaires',
                'description': 'Distribution selon le nombre d\'enfants',
                'query_code': '''
from django.db.models import Count
stats = Beneficiary.objects.values('dependents_count').annotate(count=Count('id')).order_by('dependents_count')[:6]
labels = [f"{item['dependents_count']} enfant(s)" for item in stats]
data = [item['count'] for item in stats]
result = {
    'labels': labels,
    'datasets': [{
        'label': 'Bénéficiaires',
        'data': data,
        'backgroundColor': '#8b5cf6'
    }]
}
'''
            },
            # FINANCIAL - Sources de revenus
            {
                'title': 'Distribution des sources de revenus',
                'section': 'FINANCIAL',
                'chart_type': 'bar',
                'size': 'full',
                'display_order': 11,
                'y_axis_label': 'Montant total (€)',
                'x_axis_label': 'Type de revenu',
                'description': 'Répartition des revenus par source',
                'query_code': '''
revenue_sources = {
    'RSA/Prime activité': 0,
    'Salaire': 0,
    'France Travail': 0,
    'AAH/Pension': 0,
    'Retraite/ASPA': 0,
    'Prestations familiales': 0,
    'Autres': 0
}
for snap in FinancialSnapshot.objects.all():
    revenue_sources['RSA/Prime activité'] += snap.rsa_prime_activite or 0
    revenue_sources['Salaire'] += snap.salaire or 0
    revenue_sources['France Travail'] += snap.france_travail or 0
    revenue_sources['AAH/Pension'] += snap.aah_pension_invalidite or 0
    revenue_sources['Retraite/ASPA'] += snap.retraite_aspa or 0
    revenue_sources['Prestations familiales'] += (snap.paje or 0) + (snap.af or 0) + (snap.cf or 0) + (snap.asf or 0)
    revenue_sources['Autres'] += (snap.pension_alimentaire or 0) + (snap.autres_revenus or 0) + (snap.ada or 0)
result = {
    'labels': list(revenue_sources.keys()),
    'datasets': [{
        'label': 'Revenus totaux (€)',
        'data': list(revenue_sources.values()),
        'backgroundColor': '#10b981'
    }]
}
'''
            },
            # FINANCIAL - Charges moyennes
            {
                'title': 'Répartition des charges moyennes',
                'section': 'FINANCIAL',
                'chart_type': 'bar',
                'size': 'full',
                'display_order': 12,
                'y_axis_label': 'Montant moyen (€)',
                'x_axis_label': 'Type de charge',
                'description': 'Charges moyennes par catégorie',
                'query_code': '''
charges = {
    'Loyer résiduel': 0,
    'Énergie/Eau': 0,
    'Transport': 0,
    'Crédit': 0,
    'Santé': 0,
    'Autres': 0
}
count = FinancialSnapshot.objects.count() or 1
for snap in FinancialSnapshot.objects.all():
    charges['Loyer résiduel'] += snap.loyer_residuel or 0
    charges['Énergie/Eau'] += (snap.energie or 0) + (snap.eau or 0)
    charges['Transport'] += (snap.transport_commun or 0) + (snap.carburant or 0)
    charges['Crédit'] += snap.credit_consommation or 0
    charges['Santé'] += (snap.mutuelle_privee or 0) + (snap.frais_sante_non_rembourses or 0)
    charges['Autres'] += (snap.dettes_diverses or 0) + (snap.abonnements_sport_culture or 0) + (snap.frais_scolaires or 0)
for key in charges:
    charges[key] = charges[key] / count
result = {
    'labels': list(charges.keys()),
    'datasets': [{
        'label': 'Charges moyennes (€)',
        'data': list(charges.values()),
        'backgroundColor': '#ef4444'
    }]
}
'''
            },
            # FINANCIAL - Revenus vs Charges
            {
                'title': 'Évolution Revenus vs Charges',
                'section': 'FINANCIAL',
                'chart_type': 'line',
                'size': 'full',
                'display_order': 13,
                'y_axis_label': 'Montant moyen (€)',
                'x_axis_label': 'Mois',
                'description': 'Comparaison de l\'évolution des revenus et charges',
                'query_code': '''
today = datetime.now().date()
labels = []
revenus_data = []
charges_data = []
for i in range(5, -1, -1):
    month_date = today - timedelta(days=30*i)
    labels.append(month_date.strftime('%b %Y'))
    snapshots = FinancialSnapshot.objects.filter(
        date__year=month_date.year,
        date__month=month_date.month
    )
    total_rev = 0
    total_chg = 0
    count = 0
    for snap in snapshots:
        total_rev += (snap.rsa_prime_activite or 0) + (snap.salaire or 0) + (snap.france_travail or 0) + (snap.aah_pension_invalidite or 0)
        total_chg += (snap.loyer_residuel or 0) + (snap.energie or 0) + (snap.eau or 0) + (snap.transport_commun or 0) + (snap.carburant or 0)
        count += 1
    revenus_data.append(total_rev / count if count > 0 else 0)
    charges_data.append(total_chg / count if count > 0 else 0)
result = {
    'labels': labels,
    'datasets': [
        {
            'label': 'Revenus moyens',
            'data': revenus_data,
            'borderColor': '#10b981',
            'backgroundColor': 'rgba(16, 185, 129, 0.1)',
            'tension': 0.3
        },
        {
            'label': 'Charges moyennes',
            'data': charges_data,
            'borderColor': '#ef4444',
            'backgroundColor': 'rgba(239, 68, 68, 0.1)',
            'tension': 0.3
        }
    ]
}
'''
            },
            # OPERATIONAL - Taux de présence RDV
            {
                'title': 'Statut des rendez-vous',
                'section': 'OPERATIONAL',
                'chart_type': 'bar',
                'size': 'full',
                'display_order': 14,
                'y_axis_label': 'Nombre de rendez-vous',
                'description': 'Répartition des rendez-vous par statut',
                'query_code': '''
from django.db.models import Count
stats = Appointment.objects.values('status').annotate(count=Count('id')).order_by('-count')
status_labels = {
    'SCHEDULED': 'Programmé',
    'CONFIRMED': 'Confirmé',
    'COMPLETED': 'Complété',
    'CANCELLED': 'Annulé',
    'NO_SHOW': 'Absent'
}
labels = [status_labels.get(item['status'], item['status']) for item in stats]
data = [item['count'] for item in stats]
result = {
    'labels': labels,
    'datasets': [{
        'label': 'Rendez-vous',
        'data': data,
        'backgroundColor': '#8b5cf6'
    }]
}
'''
            },
            # OPERATIONAL - Interactions par bénéficiaire
            {
                'title': 'Nombre moyen d\'interactions par bénéficiaire',
                'section': 'OPERATIONAL',
                'chart_type': 'bar',
                'size': 'half',
                'display_order': 15,
                'y_axis_label': 'Nombre d\'interactions',
                'description': 'Répartition du nombre d\'interactions',
                'query_code': '''
from django.db.models import Count
interaction_counts = {'0': 0, '1-2': 0, '3-5': 0, '6-10': 0, '10+': 0}
beneficiaries = Beneficiary.objects.annotate(num_interactions=Count('interactions'))
for ben in beneficiaries:
    count = ben.num_interactions
    if count == 0:
        interaction_counts['0'] += 1
    elif count <= 2:
        interaction_counts['1-2'] += 1
    elif count <= 5:
        interaction_counts['3-5'] += 1
    elif count <= 10:
        interaction_counts['6-10'] += 1
    else:
        interaction_counts['10+'] += 1
result = {
    'labels': list(interaction_counts.keys()),
    'datasets': [{
        'label': 'Bénéficiaires',
        'data': list(interaction_counts.values()),
        'backgroundColor': '#8b5cf6'
    }]
}
'''
            },
            # TRENDS - Nouvelles inscriptions
            {
                'title': 'Nouvelles inscriptions mensuelles',
                'section': 'TRENDS',
                'chart_type': 'bar',
                'size': 'full',
                'display_order': 16,
                'y_axis_label': 'Nouveaux bénéficiaires',
                'x_axis_label': 'Mois',
                'description': 'Évolution du nombre de nouvelles inscriptions',
                'query_code': '''
today = datetime.now().date()
labels = []
data = []
for i in range(11, -1, -1):
    month_date = today - timedelta(days=30*i)
    labels.append(month_date.strftime('%b %Y'))
    count = Beneficiary.objects.filter(
        created_at__year=month_date.year,
        created_at__month=month_date.month
    ).count()
    data.append(count)
result = {
    'labels': labels,
    'datasets': [{
        'label': 'Nouvelles inscriptions',
        'data': data,
        'backgroundColor': '#3b82f6'
    }]
}
'''
            },
            # TRENDS - Actifs vs Inactifs
            {
                'title': 'Évolution Bénéficiaires actifs vs inactifs',
                'section': 'TRENDS',
                'chart_type': 'line',
                'size': 'full',
                'display_order': 17,
                'y_axis_label': 'Nombre de bénéficiaires',
                'x_axis_label': 'Mois',
                'description': 'Suivi de l\'activité des bénéficiaires (interaction < 3 mois = actif)',
                'query_code': '''
today = datetime.now().date()
labels = []
actifs_data = []
inactifs_data = []
for i in range(5, -1, -1):
    month_date = today - timedelta(days=30*i)
    labels.append(month_date.strftime('%b %Y'))
    cutoff_date = month_date - timedelta(days=90)  # 3 mois
    actifs = 0
    inactifs = 0
    for ben in Beneficiary.objects.filter(created_at__lte=month_date):
        last_interaction = ben.interactions.order_by('-created_at').first()
        if last_interaction and last_interaction.created_at.date() >= cutoff_date:
            actifs += 1
        else:
            inactifs += 1
    actifs_data.append(actifs)
    inactifs_data.append(inactifs)
result = {
    'labels': labels,
    'datasets': [
        {
            'label': 'Actifs',
            'data': actifs_data,
            'borderColor': '#10b981',
            'backgroundColor': 'rgba(16, 185, 129, 0.1)',
            'tension': 0.3
        },
        {
            'label': 'Inactifs',
            'data': inactifs_data,
            'borderColor': '#f59e0b',
            'backgroundColor': 'rgba(245, 158, 11, 0.1)',
            'tension': 0.3
        }
    ]
}
'''
            },
            # IMPACT - Familles vs Individus
            {
                'title': 'Bénéficiaires avec famille vs sans famille',
                'section': 'IMPACT',
                'chart_type': 'pie',
                'size': 'half',
                'display_order': 18,
                'description': 'Impact sur les familles',
                'query_code': '''
from django.db.models import Count
ben_with_children = Beneficiary.objects.annotate(num_children=Count('children')).filter(num_children__gt=0).count()
ben_without_children = Beneficiary.objects.annotate(num_children=Count('children')).filter(num_children=0).count()
result = {
    'labels': ['Avec enfants', 'Sans enfants'],
    'datasets': [{
        'label': 'Bénéficiaires',
        'data': [ben_with_children, ben_without_children],
        'backgroundColor': ['#10b981', '#3b82f6']
    }]
}
'''
            },
            # IMPACT - Taux de suivi
            {
                'title': 'Taux de complétion des suivis',
                'section': 'IMPACT',
                'chart_type': 'doughnut',
                'size': 'half',
                'display_order': 19,
                'description': 'Pourcentage de suivis complétés vs en attente',
                'query_code': '''
from django.db.models import Q
total_interactions = Interaction.objects.filter(follow_up_required=True).count()
# Considérer comme complété si follow_up_notes n'est pas vide
completed = Interaction.objects.filter(follow_up_required=True).exclude(Q(follow_up_notes='') | Q(follow_up_notes__isnull=True)).count()
pending = total_interactions - completed
result = {
    'labels': ['Suivis complétés', 'Suivis en attente'],
    'datasets': [{
        'label': 'Suivis',
        'data': [completed, pending],
        'backgroundColor': ['#10b981', '#f59e0b']
    }]
}
'''
            },
            # DEMOGRAPHIC - Métiers / Compétences
            {
                'title': 'Bénéficiaires avec métier/compétence déclarée',
                'section': 'DEMOGRAPHIC',
                'chart_type': 'pie',
                'size': 'half',
                'display_order': 20,
                'description': 'Proportion de bénéficiaires avec un métier ou savoir-faire',
                'query_code': '''
with_occupation = Beneficiary.objects.exclude(occupation='').exclude(occupation__isnull=True).count()
without_occupation = Beneficiary.objects.filter(occupation='').count() + Beneficiary.objects.filter(occupation__isnull=True).count()
result = {
    'labels': ['Avec métier/compétence', 'Sans métier déclaré'],
    'datasets': [{
        'label': 'Bénéficiaires',
        'data': [with_occupation, without_occupation],
        'backgroundColor': ['#10b981', '#94a3b8']
    }]
}
'''
            },
            # OPERATIONAL - Délai de réponse
            {
                'title': 'Délai moyen entre création et premier contact',
                'section': 'OPERATIONAL',
                'chart_type': 'bar',
                'size': 'full',
                'display_order': 21,
                'y_axis_label': 'Jours',
                'x_axis_label': 'Mois',
                'description': 'Temps de réponse aux nouveaux bénéficiaires',
                'query_code': '''
from django.db.models import Avg
today = datetime.now().date()
labels = []
data = []
# Tous les bénéficiaires avec au moins une interaction
all_beneficiaries = Beneficiary.objects.all()
delays = []
for ben in all_beneficiaries:
    first_interaction = ben.interactions.order_by('created_at').first()
    if first_interaction:
        days = (first_interaction.created_at.date() - ben.created_at.date()).days
        if days >= 0:  # Seulement les délais positifs
            delays.append(days)
avg_delay = sum(delays) / len(delays) if delays else 0
result = {
    'labels': ['Délai moyen global'],
    'datasets': [{
        'label': 'Jours',
        'data': [avg_delay],
        'backgroundColor': '#8b5cf6'
    }]
}
'''
            },
            # ADVANCED - Heatmap rendez-vous
            {
                'title': 'Heatmap des rendez-vous (Jour × Heure)',
                'section': 'ADVANCED',
                'chart_type': 'bar',
                'size': 'full',
                'display_order': 22,
                'y_axis_label': 'Nombre de RDV',
                'x_axis_label': 'Jour de la semaine',
                'description': 'Distribution des rendez-vous par jour et plage horaire',
                'query_code': '''
days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
morning = [0] * 7  # 8h-12h
afternoon = [0] * 7  # 14h-18h
for apt in Appointment.objects.all():
    if apt.appointment_date:
        day_index = apt.appointment_date.weekday()
        if apt.start_time:
            hour = apt.start_time.hour
            if 8 <= hour < 12:
                morning[day_index] += 1
            elif 14 <= hour < 18:
                afternoon[day_index] += 1
result = {
    'labels': days,
    'datasets': [
        {
            'label': 'Matin (8h-12h)',
            'data': morning,
            'backgroundColor': '#3b82f6'
        },
        {
            'label': 'Après-midi (14h-18h)',
            'data': afternoon,
            'backgroundColor': '#10b981'
        }
    ]
}
'''
            },
            # ADVANCED - Corrélation logement/revenus
            {
                'title': 'Revenus moyens par type de logement',
                'section': 'ADVANCED',
                'chart_type': 'bar',
                'size': 'full',
                'display_order': 23,
                'y_axis_label': 'Revenu moyen (€)',
                'x_axis_label': 'Type de logement',
                'description': 'Corrélation entre situation de logement et revenus',
                'query_code': '''
housing_revenue = {}
for ben in Beneficiary.objects.all():
    housing = ben.housing_status or 'Non renseigné'
    snapshot = ben.financial_snapshots.order_by('-date').first()
    if snapshot:
        total_rev = (snapshot.rsa_prime_activite or 0) + (snapshot.salaire or 0) + (snapshot.france_travail or 0)
        if housing not in housing_revenue:
            housing_revenue[housing] = {'total': 0, 'count': 0}
        housing_revenue[housing]['total'] += total_rev
        housing_revenue[housing]['count'] += 1
labels = []
data = []
for housing, values in housing_revenue.items():
    labels.append(housing)
    avg = values['total'] / values['count'] if values['count'] > 0 else 0
    data.append(avg)
result = {
    'labels': labels,
    'datasets': [{
        'label': 'Revenu moyen (€)',
        'data': data,
        'backgroundColor': '#8b5cf6'
    }]
}
'''
            },
            # TRENDS - Taux de rétention
            {
                'title': 'Taux de rétention des bénéficiaires',
                'section': 'TRENDS',
                'chart_type': 'line',
                'size': 'full',
                'display_order': 24,
                'y_axis_label': 'Pourcentage',
                'x_axis_label': 'Mois',
                'description': 'Pourcentage de bénéficiaires toujours actifs après X mois',
                'query_code': '''
today = datetime.now().date()
labels = []
data = []
for i in range(5, -1, -1):
    month_date = today - timedelta(days=30*i)
    labels.append(month_date.strftime('%b %Y'))
    # Bénéficiaires inscrits ce mois-là
    month_beneficiaries = Beneficiary.objects.filter(
        created_at__year=month_date.year,
        created_at__month=month_date.month
    )
    total = month_beneficiaries.count()
    still_active = 0
    cutoff = today - timedelta(days=90)
    for ben in month_beneficiaries:
        last_int = ben.interactions.order_by('-created_at').first()
        if last_int and last_int.created_at.date() >= cutoff:
            still_active += 1
    retention_rate = (still_active / total * 100) if total > 0 else 0
    data.append(retention_rate)
result = {
    'labels': labels,
    'datasets': [{
        'label': 'Taux de rétention (%)',
        'data': data,
        'borderColor': '#10b981',
        'backgroundColor': 'rgba(16, 185, 129, 0.1)',
        'tension': 0.3
    }]
}
'''
            },
            # OPERATIONAL - Types de suivis
            {
                'title': 'Répartition des suivis par type d\'aide',
                'section': 'OPERATIONAL',
                'chart_type': 'bar',
                'size': 'full',
                'display_order': 25,
                'y_axis_label': 'Nombre de suivis',
                'description': 'Types d\'aides nécessitant un suivi',
                'query_code': '''
from django.db.models import Count
stats = Interaction.objects.filter(follow_up_required=True).values('interaction_type').annotate(count=Count('id'))
labels = [item['interaction_type'] for item in stats]
data = [item['count'] for item in stats]
result = {
    'labels': labels,
    'datasets': [{
        'label': 'Suivis requis',
        'data': data,
        'backgroundColor': '#f59e0b'
    }]
}
'''
            },
            # IMPACT - Évolution enfants pris en charge
            {
                'title': 'Évolution du nombre d\'enfants pris en charge',
                'section': 'IMPACT',
                'chart_type': 'line',
                'size': 'full',
                'display_order': 26,
                'y_axis_label': 'Nombre d\'enfants',
                'x_axis_label': 'Mois',
                'description': 'Impact sur les familles et enfants',
                'query_code': '''
today = datetime.now().date()
labels = []
data = []
for i in range(11, -1, -1):
    month_date = today - timedelta(days=30*i)
    month_start = month_date.replace(day=1)
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
    month_end_datetime = timezone.make_aware(datetime.combine(month_end, datetime.max.time()))
    labels.append(month_date.strftime('%b %Y'))
    count = Child.objects.filter(created_at__lte=month_end_datetime).count()
    data.append(count)
result = {
    'labels': labels,
    'datasets': [{
        'label': 'Enfants',
        'data': data,
        'borderColor': '#ec4899',
        'backgroundColor': 'rgba(236, 72, 153, 0.1)',
        'tension': 0.3,
        'fill': True
    }]
}
'''
            }
        ]

        charts_count = 0
        for chart_data in charts_data:
            ChartConfig.objects.create(**chart_data)
            charts_count += 1

        return charts_count