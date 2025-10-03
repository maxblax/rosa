from django.urls import path
from . import views

app_name = 'dons'

urlpatterns = [
    path('', views.DonationListView.as_view(), name='list'),
    path('analytics/', views.DonationAnalyticsView.as_view(), name='analytics'),
    path('create/', views.DonationCreateView.as_view(), name='create'),
    path('<int:pk>/', views.DonationDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.DonationUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.DonationDeleteView.as_view(), name='delete'),
]
