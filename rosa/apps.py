from django.apps import AppConfig


class rosaConfig(AppConfig):
    name = 'rosa'
    verbose_name = 'rosa Configuration'

    def ready(self):
        """Configure Django admin site when app is ready"""
        from django.contrib import admin
        from django.conf import settings

        admin.site.site_header = f"{settings.ASSOCIATION_NAME} - Administration"
        admin.site.site_title = f"{settings.ASSOCIATION_NAME}"
        admin.site.index_title = f"Gestion de {settings.ASSOCIATION_NAME}"
