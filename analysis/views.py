"""
Vues pour l'application d'analyse
"""
import json
from decimal import Decimal
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import ChartConfig


def convert_decimals(obj):
    """Convertit récursivement les Decimal en float pour la sérialisation JSON"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    return obj


def user_can_access_analysis(user):
    """
    Vérifie si l'utilisateur peut accéder aux analyses.
    Accessible uniquement aux ADMIN, EMPLOYEE et VOLUNTEER_GOVERNANCE.
    """
    if user.is_superuser:
        return True

    try:
        volunteer = user.volunteer_profile
        return volunteer and volunteer.role in ['ADMIN', 'EMPLOYEE', 'VOLUNTEER_GOVERNANCE']
    except AttributeError:
        return False


@login_required
def analysis_dashboard(request):
    """
    Page principale d'analyse avec tous les graphiques configurés.
    Accessible uniquement aux utilisateurs autorisés.
    """
    # Vérification des permissions
    if not user_can_access_analysis(request.user):
        return HttpResponseForbidden(
            "Vous n'avez pas les permissions nécessaires pour accéder aux analyses. "
            "Cette section est réservée aux administrateurs, salariés et bénévoles de gouvernance."
        )

    # Récupérer tous les graphiques actifs groupés par section
    charts = ChartConfig.objects.filter(is_active=True).order_by('section', 'display_order', 'title')

    # Grouper par section
    sections_data = {}
    for chart in charts:
        data = chart.get_chart_data()

        chart_info = {
            'id': chart.id,
            'title': chart.title,
            'description': chart.description,
            'chart_type': chart.chart_type,
            'size': chart.size,
            'y_axis_label': chart.y_axis_label,
            'x_axis_label': chart.x_axis_label,
            'data_json': json.dumps(convert_decimals(data)),
            'has_error': 'error' in data
        }

        if 'error' in data:
            chart_info['error_message'] = data['error']

        # Grouper par section
        section_key = chart.section
        section_label = chart.get_section_display()

        if section_key not in sections_data:
            sections_data[section_key] = {
                'label': section_label,
                'charts': []
            }

        sections_data[section_key]['charts'].append(chart_info)

    # Ordre des sections pour l'affichage
    section_order = ['IMPACT', 'DEMOGRAPHIC', 'FINANCIAL', 'OPERATIrosaL', 'TRENDS', 'ADVANCED']
    ordered_sections = [
        {'key': key, 'label': sections_data[key]['label'], 'charts': sections_data[key]['charts']}
        for key in section_order if key in sections_data
    ]

    context = {
        'sections': ordered_sections,
        'can_export': True,  # Pour activer les boutons d'export plus tard
    }

    return render(request, 'analysis/dashboard.html', context)
