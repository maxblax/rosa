from django.urls import path
from . import views

app_name = 'calendar'

urlpatterns = [
    # Vue principale du calendrier
    path('', views.CalendarView.as_view(), name='main'),

    # Vues par type
    path('day/', views.CalendarDayView.as_view(), name='day'),
    path('week/', views.CalendarWeekView.as_view(), name='week'),
    path('month/', views.CalendarMonthView.as_view(), name='month'),

    # Vue globale pour admin/salariés
    path('global/', views.GlobalCalendarView.as_view(), name='global'),

    # Gestion des disponibilités
    path('availability/', views.AvailabilityListView.as_view(), name='availability_list'),
    path('availability/create/', views.AvailabilityCreateView.as_view(), name='availability_create'),
    path('availability/<int:pk>/', views.AvailabilityDetailView.as_view(), name='availability_detail'),
    path('availability/<int:pk>/edit/', views.AvailabilityEditView.as_view(), name='availability_edit'),
    path('availability/<int:pk>/delete/', views.AvailabilityDeleteView.as_view(), name='availability_delete'),

    # Panels HTMX pour édition de disponibilités
    path('availability/<int:pk>/edit-panel/', views.availability_edit_panel, name='availability_edit_panel'),
    path('availability/new-panel/', views.availability_new_panel, name='availability_new_panel'),

    # Gestion des rendez-vous
    path('appointments/', views.AppointmentListView.as_view(), name='appointment_list'),
    path('appointments/create/', views.AppointmentCreateView.as_view(), name='appointment_create'),
    path('appointments/<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment_detail'),
    path('appointments/<int:pk>/edit/', views.AppointmentEditView.as_view(), name='appointment_edit'),
    path('appointments/<int:pk>/delete/', views.AppointmentDeleteView.as_view(), name='appointment_delete'),
    path('appointments/<int:pk>/status/', views.appointment_change_status, name='appointment_status'),

    # API endpoints pour HTMX
    path('api/slots/', views.api_availability_slots, name='api_slots'),
    path('api/appointments/', views.api_appointments, name='api_appointments'),
    path('api/calendar-data/', views.api_calendar_data, name='api_calendar_data'),
    path('api/volunteer-availability/', views.volunteer_availability_api, name='api_volunteer_availability'),
    path('api/available-volunteers/', views.available_volunteers_api, name='api_available_volunteers'),

    # Paramètres du calendrier
    path('settings/', views.CalendarSettingsView.as_view(), name='settings'),
]