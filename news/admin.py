from django.contrib import admin
from .models import News


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'news_type', 'publication_date', 'is_pinned', 'created_at']
    list_filter = ['news_type', 'is_pinned', 'publication_date', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-is_pinned', '-publication_date']

    fieldsets = (
        ('Informations principales', {
            'fields': ('title', 'news_type', 'description')
        }),
        ('Options', {
            'fields': ('is_pinned',)
        }),
        ('Métadonnées', {
            'fields': ('publication_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['publication_date', 'created_at', 'updated_at']
