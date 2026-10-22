from django.db import migrations

DESCRIPTIONS = {
    'Épicerie - panier solidaire': "Trois passages pour toute la famille, un par semaine maximum, sur les ouvertures de l'épicerie.",
    'Vestiaire solidaire': "Un passage le jeudi après-midi, 20 personnes maximum, 2 adultes et 2 enfants par date.",
}

OLD = "Trois distributions consécutives pour toute la famille, le mercredi après-midi."


def forwards(apps, schema_editor):
    Service = apps.get_model('services', 'Service')
    service = Service.objects.filter(name='Épicerie - panier solidaire', description=OLD).first()
    if service:
        service.description = DESCRIPTIONS[service.name]
        service.save(update_fields=['description'])


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0003_schedule_slots_and_tickets'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
