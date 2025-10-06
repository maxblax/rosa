"""
URL configuration for rosa project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings

# Import for home view
from rosa.views import home

urlpatterns = [
    path(f'{settings.ADMIN_URL}/', admin.site.urls),
    path('auth/', include('rosa.auth_urls')),
    path('beneficiaires/', include('beneficiaries.urls')),
    path('benevoles/', include('volunteers.urls')),
    path('calendrier/', include('calendar_app.urls')),
    path('partenaires/', include('partners.urls')),
    path('stock/', include('stock.urls')),
    path('analyses/', include('analysis.urls')),
    path('dons/', include('dons.urls')),
    path('', home, name='home'),
]
