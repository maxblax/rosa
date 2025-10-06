from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.conf import settings
from django.urls import resolve


class AuthenticationMiddleware:
    """Middleware pour gérer l'authentification avec mode dev"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs publiques (pas besoin d'authentification)
        public_urls = [
            'auth:login',
            'auth:logout',
            'admin:index',
            'admin:login',
            'admin:logout',
        ]

        # URLs publiques par pattern
        public_patterns = [
            '/admin/',
            '/auth/',
            '/static/',
            '/media/',
        ]

        # En mode dev, bypass l'authentification
        if settings.DEV_MODE:
            return self.get_response(request)

        # Vérifier si l'URL est publique
        try:
            current_url = resolve(request.path_info)
            url_name = f"{current_url.namespace}:{current_url.url_name}" if current_url.namespace else current_url.url_name

            if url_name in public_urls:
                return self.get_response(request)
        except:
            pass

        # Vérifier les patterns publics
        for pattern in public_patterns:
            if request.path_info.startswith(pattern):
                return self.get_response(request)

        # Si l'utilisateur n'est pas connecté, rediriger vers login
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        return self.get_response(request)