from datetime import time

from django.db import migrations

CATALOGUE = [
    # (nom, fonctionnement, catégorie, options)
    ('Accompagnement social', 'SIMPLE', 'INTERNAL', {}),
    ('Épicerie - panier solidaire', 'DISTRIBUTION', 'INTERNAL', {
        'description': "Trois distributions consécutives pour toute la famille, le mercredi après-midi.",
        'session_weekday': 2, 'session_start': time(14, 0), 'session_end': time(17, 0),
        'sessions_per_registration': 3, 'scheduling': 'AUTO', 'capacity_unit': 'FAMILIES',
    }),
    ('Vestiaire solidaire', 'DISTRIBUTION', 'INTERNAL', {
        'description': "Un passage le jeudi après-midi, 20 personnes maximum, 2 adultes et 2 enfants par date.",
        'session_weekday': 3, 'session_start': time(14, 0), 'session_end': time(17, 0),
        'sessions_per_registration': 1, 'scheduling': 'CHOICE', 'session_capacity': 20,
        'capacity_unit': 'PERSONS', 'max_adults_per_booking': 2, 'max_children_per_booking': 2,
    }),
    ('Antenne médicale (Croix-Rouge)', 'SIMPLE', 'INTERNAL', {
        'description': "Orientation vers l'antenne médicale en partenariat avec la Croix-Rouge française.",
    }),
    ('Ateliers sociolinguistiques (adultes)', 'SIMPLE', 'INTERNAL', {}),
    ('Aide aux devoirs', 'SIMPLE', 'INTERNAL', {}),
    ('Soutien à la parentalité', 'SIMPLE', 'INTERNAL', {}),
    ('Visites aux personnes âgées isolées', 'SIMPLE', 'INTERNAL', {}),
    ('Atelier couture', 'SIMPLE', 'INTERNAL', {}),
    ('Devenir bénévole', 'SIMPLE', 'INTERNAL', {}),
    ('Aide financière', 'FINANCIAL', 'SUPPORT', {
        'description': "Demande instruite en entretien, validée ou refusée par un administrateur.",
    }),
    ("Kit d'hygiène (don)", 'SIMPLE', 'SUPPORT', {}),
    ('Couches (don)', 'SIMPLE', 'SUPPORT', {}),
    ('Autre soutien', 'SIMPLE', 'SUPPORT', {'requires_details': True}),
    ('Orientation externe', 'SIMPLE', 'EXTERNAL', {
        'description': "Orientation vers un partenaire extérieur (avocat, CCAS, PMI...).",
        'requires_details': True,
    }),
]


def create_catalogue(apps, schema_editor):
    Service = apps.get_model('services', 'Service')
    Partner = apps.get_model('partners', 'Partner')
    if Service.objects.exists():
        return
    red_cross = Partner.objects.filter(name__icontains='croix').first()
    for order, (name, kind, category, options) in enumerate(CATALOGUE, start=1):
        options = dict(options)
        if name.startswith('Antenne médicale') and red_cross:
            options['partner'] = red_cross
        Service.objects.create(name=name, kind=kind, category=category, order=order * 10, **options)


def migrate_legacy_aids(apps, schema_editor):
    """Reprend les secours saisis dans les entretiens comme des aides versées."""
    Interaction = apps.get_model('beneficiaries', 'Interaction')
    FinancialAidRequest = apps.get_model('services', 'FinancialAidRequest')
    legacy = Interaction.objects.filter(financial_aid_amount__gt=0)
    for interaction in legacy:
        if FinancialAidRequest.objects.filter(interaction=interaction).exists():
            continue
        FinancialAidRequest.objects.create(
            beneficiary_id=interaction.beneficiary_id,
            interaction=interaction,
            amount=interaction.financial_aid_amount,
            nature='AUTRE',
            reason=interaction.financial_aid_details or 'Secours saisi dans un entretien (reprise)',
            status='PAID',
            requested_by_id=interaction.user_id,
            decided_by_id=interaction.user_id,
            decided_at=interaction.created_at,
            paid_at=interaction.created_at.date(),
            payment_notes="Reprise automatique de l'historique des entretiens.",
        )


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0001_initial'),
        ('partners', '0001_initial'),
        ('beneficiaries', '0016_alter_financialsnapshot_aah_pension_invalidite_and_more'),
    ]

    operations = [
        migrations.RunPython(create_catalogue, migrations.RunPython.noop),
        migrations.RunPython(migrate_legacy_aids, migrations.RunPython.noop),
    ]
