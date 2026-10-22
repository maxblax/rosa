from django.urls import path

from . import views

app_name = 'services'

urlpatterns = [
    path('', views.services_home, name='home'),
    path('statistiques/', views.stats, name='stats'),

    # Distributions
    path('distributions/<int:service_pk>/', views.week_view, name='week'),
    path('distributions/<int:service_pk>/creneaux/', views.slot_save, name='slot_create'),
    path('distributions/<int:service_pk>/creneaux/<int:pk>/', views.slot_save, name='slot_edit'),
    path('distributions/<int:service_pk>/creneaux/<int:pk>/supprimer/', views.slot_delete, name='slot_delete'),
    path('distributions/<int:service_pk>/sessions/ajouter/', views.session_add, name='session_add'),
    path('sessions/<int:pk>/', views.session_detail, name='session_detail'),
    path('sessions/<int:pk>/modifier/', views.session_edit, name='session_edit'),
    path('sessions/<int:pk>/annuler/', views.session_toggle, name='session_toggle'),
    path('reservations/<int:pk>/pointer/', views.booking_mark, name='booking_mark'),
    path('reservations/<int:pk>/annuler/', views.booking_cancel, name='booking_cancel'),
    path('inscriptions/<int:pk>/reserver/', views.booking_assign, name='booking_assign'),

    # Inscriptions
    path('inscriptions/<int:pk>/annuler/', views.registration_cancel, name='registration_cancel'),
    path('inscriptions/<int:pk>/realise/', views.registration_done, name='registration_done'),
    path('inscriptions/<int:pk>/bon/', views.registration_voucher, name='registration_voucher'),

    # Aides financières
    path('aides/', views.aid_list, name='aid_list'),
    path('aides/<int:pk>/', views.aid_detail, name='aid_detail'),

    # Catalogue
    path('catalogue/', views.ServiceListView.as_view(), name='catalogue'),
    path('catalogue/nouveau/', views.ServiceCreateView.as_view(), name='service_create'),
    path('catalogue/<int:pk>/modifier/', views.ServiceUpdateView.as_view(), name='service_edit'),
]
