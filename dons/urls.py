from django.urls import path
from . import views

app_name = 'dons'

urlpatterns = [
    path('', views.donationListView.as_view(), name='list'),
    path('analytics/', views.DrosatirosanalyticsView.as_view(), name='analytics'),
    path('create/', views.donationCreateView.as_view(), name='create'),
    path('<int:pk>/', views.donationDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.donationUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.donationDeleteView.as_view(), name='delete'),
]
