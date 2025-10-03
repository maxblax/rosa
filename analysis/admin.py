from django.contrib import admin
from .models import ChartConfig


@admin.register(ChartConfig)
class ChartConfigAdmin(admin.ModelAdmin):
    list_display = ['title', 'section', 'chart_type', 'size', 'display_order', 'is_active', 'updated_at']
    list_filter = ['section', 'chart_type', 'size', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['section', 'display_order', 'title']
    list_editable = ['display_order', 'is_active']

    fieldsets = (
        ('Configuration de base', {
            'fields': ('title', 'description', 'section', 'chart_type')
        }),
        ('Position et affichage', {
            'fields': ('display_order', 'size', 'is_active')
        }),
        ('Requête de données', {
            'fields': ('query_code',),
            'description': '''
            <strong>Exemples de code :</strong><br><br>

            <strong>1. Évolution mensuelle des bénéficiaires :</strong><br>
            <pre>
today = datetime.now().date()
labels = []
data = []
for i in range(5, -1, -1):
    month_date = today - timedelta(days=30*i)
    labels.append(month_date.strftime('%b %Y'))
    count = Beneficiary.objects.filter(created_at__lte=month_date).count()
    data.append(count)
result = {
    'labels': labels,
    'datasets': [{
        'label': 'Nombre de bénéficiaires',
        'data': data,
        'borderColor': 'rgb(59, 130, 246)',
        'backgroundColor': 'rgba(59, 130, 246, 0.1)'
    }]
}
            </pre><br>

            <strong>2. Répartition par statut familial :</strong><br>
            <pre>
from django.db.models import Count
stats = Beneficiary.objects.values('family_status').annotate(count=Count('id'))
labels = [item['family_status'] for item in stats]
data = [item['count'] for item in stats]
result = {
    'labels': labels,
    'datasets': [{
        'label': 'Bénéficiaires',
        'data': data,
        'backgroundColor': ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
    }]
}
            </pre><br>

            <strong>Variables disponibles :</strong> Count, Sum, Avg, Q, timezone, datetime, timedelta,
            Beneficiary, Interaction, FinancialSnapshot, Child, Appointment, Volunteer, StockItem, StockMovement
            '''
        }),
        ('Labels des axes', {
            'fields': ('x_axis_label', 'y_axis_label')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def get_queryset(self, request):
        return super().get_queryset(request)
