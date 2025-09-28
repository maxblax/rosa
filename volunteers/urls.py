from django.urls import path
from . import views

app_name = 'volunteers'

urlpatterns = [
    # Liste et recherche
    path('', views.VolunteerListView.as_view(), name='list'),
    path('search/', views.volunteer_search_autocomplete, name='search'),

    # CRUD bénévoles
    path('create/', views.VolunteerCreateView.as_view(), name='create'),
    path('<int:pk>/', views.VolunteerDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.VolunteerUpdateView.as_view(), name='edit'),

    # Suivi des heures
    path('<int:volunteer_pk>/time-tracking/create/', views.TimeTrackingCreateView.as_view(), name='time_tracking_create'),
    path('<int:volunteer_pk>/time-tracking/<int:pk>/edit/', views.TimeTrackingUpdateView.as_view(), name='time_tracking_edit'),
]