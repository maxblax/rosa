"""
URL configuration pour l'application analysis
"""
from django.urls import path
from . import views

app_name = 'analysis'

urlpatterns = [
    path('', views.analysis_dashboard, name='dashboard'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
    path('export/ppt/', views.export_ppt, name='export_ppt'),
]
