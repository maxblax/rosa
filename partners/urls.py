from django.urls import path
from . import views

app_name = 'partners'

urlpatterns = [
    path('', views.PartnerListView.as_view(), name='list'),
    path('new/', views.PartnerCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.PartnerUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.PartnerDeleteView.as_view(), name='delete'),
    path('api/services/', views.get_all_services, name='api_services'),
]
