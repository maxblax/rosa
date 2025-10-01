from django.contrib import admin
from django.utils.html import format_html
from .models import Volunteer


@admin.register(Volunteer)
class VolunteerAdmin(admin.ModelAdmin):
    list_display = [
        'full_name_display',
        'role_badge',
        'status_badge',
        'phone',
        'age_display',
        'join_date',
        'last_activity'
    ]
    list_filter = ['role', 'status', 'join_date', 'created_at']
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'phone',
        'skills'
    ]
    ordering = ['user__last_name', 'user__first_name']
    date_hierarchy = 'join_date'

    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Informations personnelles', {
            'fields': ('civility', 'birth_date', 'phone', 'address')
        }),
        ('Rôle et statut', {
            'fields': ('role', 'status')
        }),
        ('Compétences', {
            'fields': ('skills',),
            'classes': ('collapse',)
        }),
        ('Dates importantes', {
            'fields': ('join_date', 'last_activity'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def full_name_display(self, obj):
        """Affiche le nom complet du bénévole"""
        return obj.full_name
    full_name_display.short_description = 'Nom complet'
    full_name_display.admin_order_field = 'user__last_name'

    def role_badge(self, obj):
        """Affiche le rôle avec un badge coloré"""
        colors = {
            'ADMIN': '#dc2626',  # Rouge
            'EMPLOYEE': '#2563eb',  # Bleu
            'VOLUNTEER_INTERVIEW': '#059669',  # Vert
            'VOLUNTEER_GOVERNANCE': '#7c3aed',  # Violet
        }
        color = colors.get(obj.role, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_badge.short_description = 'Rôle'
    role_badge.admin_order_field = 'role'

    def status_badge(self, obj):
        """Affiche le statut avec un badge coloré"""
        colors = {
            'ACTIVE': '#059669',  # Vert
            'INACTIVE': '#6b7280',  # Gris
            'SUSPENDED': '#dc2626',  # Rouge
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    status_badge.admin_order_field = 'status'

    def age_display(self, obj):
        """Affiche l'âge du bénévole"""
        if obj.age:
            return f"{obj.age} ans"
        return "—"
    age_display.short_description = 'Âge'

    def get_queryset(self, request):
        """Optimise les requêtes en préchargeant les relations"""
        queryset = super().get_queryset(request)
        return queryset.select_related('user')
