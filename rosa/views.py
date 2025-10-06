"""
Vue home du projet rosa
"""
import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Q
from calendar_app.models import Appointment, VolunteerCalendar
from beneficiaries.models import Beneficiary, Interaction
from news.models import News


@login_required
def home(request):
    """Page d'accueil / Tableau de bord"""
    today = timezone.now().date()
    this_month_start = today.replace(day=1)

    # 1. Prochains rendez-vous de l'utilisateur connecté (5 prochains)
    upcoming_appointments = []

    # Récupérer le calendrier de l'utilisateur connecté
    try:
        if hasattr(request.user, 'volunteer_profile') and request.user.volunteer_profile:
            volunteer_calendar = VolunteerCalendar.objects.get(volunteer=request.user.volunteer_profile)
            upcoming_appointments = Appointment.objects.filter(
                volunteer_calendar=volunteer_calendar,
                appointment_date__gte=today,
                status__in=['SCHEDULED', 'CONFIRMED']
            ).select_related(
                'beneficiary',
                'volunteer_calendar__volunteer__user'
            ).order_by('appointment_date', 'start_time')[:3]
    except (VolunteerCalendar.DoesNotExist, AttributeError):
        # L'utilisateur n'a pas de calendrier, on affiche aucun rendez-vous
        pass

    # 2. Stats des bénéficiaires
    total_beneficiaries = Beneficiary.objects.count()

    # Nouveaux ce mois
    new_this_month = Beneficiary.objects.filter(
        created_at__gte=this_month_start
    ).count()

    # Aidés récemment (avec interaction dans les 30 derniers jours)
    thirty_days_ago = today - timedelta(days=30)
    helped_recently = Beneficiary.objects.filter(
        interactions__created_at__gte=timezone.make_aware(datetime.combine(thirty_days_ago, datetime.min.time()))
    ).distinct().count()

    # Calcul des "sorties" (bénéficiaires sans interaction depuis 6 mois)
    # Note: C'est une approximation, à adapter selon vos besoins
    six_months_ago = today - timedelta(days=180)
    inactive_beneficiaries = Beneficiary.objects.exclude(
        interactions__created_at__gte=timezone.make_aware(datetime.combine(six_months_ago, datetime.min.time()))
    ).exclude(
        created_at__gte=timezone.make_aware(datetime.combine(six_months_ago, datetime.min.time()))
    ).count()

    stats = {
        'total': total_beneficiaries,
        'new_this_month': new_this_month,
        'helped_recently': helped_recently,
        'inactive': inactive_beneficiaries,
    }

    # 3. Évolution des bénéficiaires (6 derniers mois)
    evolution_data = []
    for i in range(5, -1, -1):
        # Calculer le mois ciblé
        month_date = today - timedelta(days=30 * i)
        month_start = month_date.replace(day=1)

        # Calculer la fin du mois
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)

        # Convertir en datetime aware pour la comparaison
        month_end_datetime = timezone.make_aware(datetime.combine(month_end, datetime.max.time()))

        # Compter les bénéficiaires créés jusqu'à la fin de ce mois
        count = Beneficiary.objects.filter(
            created_at__lte=month_end_datetime
        ).count()

        evolution_data.append({
            'month': month_start.strftime('%b'),
            'count': count
        })

    # 4. Dernières actualités (3 dernières)
    latest_news = News.objects.all()[:3]

    context = {
        'upcoming_appointments': upcoming_appointments,
        'stats': stats,
        'evolution_data': evolution_data,
        'evolution_data_json': json.dumps(evolution_data),
        'latest_news': latest_news,
    }

    return render(request, 'home.html', context)
