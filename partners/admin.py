from django.contrib import admin
from .models import Partner


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'get_services_count', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'email', 'phone', 'services']
    ordering = ['name']

    fieldsets = (
        ('Informations principales', {
            'fields': ('name',)
        }),
        ('Coordonnées', {
            'fields': ('address', 'phone', 'email')
        }),
        ('Services', {
            'fields': ('services',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def get_services_count(self, obj):
        """Retourne le nombre de services fournis"""
        return len(obj.get_services_list())
    get_services_count.short_description = 'Nombre de services'
