from django.urls import path
from . import views

app_name = 'beneficiaries'

urlpatterns = [
    # Vues principales
    path('', views.BeneficiaryListView.as_view(), name='list'),
    path('new/', views.BeneficiaryCreateView.as_view(), name='create'),
    path('<int:pk>/', views.BeneficiaryDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.BeneficiaryUpdateView.as_view(), name='edit'),
    
    # Snapshot financier
    path('<int:pk>/snapshot/new/', views.financial_snapshot_create_view, name='financial_snapshot_create'),
    
    # Interactions
    path('<int:beneficiary_pk>/interactions/new/', views.InteractionCreateView.as_view(), name='interaction_create'),
    path('<int:beneficiary_pk>/interactions/<int:pk>/', views.InteractionDetailView.as_view(), name='interaction_detail'),
    path('<int:beneficiary_pk>/interactions/<int:pk>/edit/', views.InteractionUpdateView.as_view(), name='interaction_edit'),
    
    # API/HTMX endpoints
    path('search/', views.beneficiary_search_autocomplete, name='search_autocomplete'),
] 