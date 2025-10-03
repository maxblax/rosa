"""
URL configuration pour l'application analysis
"""
from django.urls import path
from . import views

app_name = 'analysis'

urlpatterns = [
    path('', views.analysis_dashboard, name='dashboard'),
]
