from django.urls import path

from . import views

app_name = 'services'

urlpatterns = [
    path('', views.services_home, name='home'),
    path('statistiques/', views.stats, name='stats'),

    # Distributions
    path('distributions/<int:service_pk>/', views.session_list, name='session_list'),
    path('sessions/<int:pk>/', views.session_detail, name='session_detail'),
    path('reservations/<int:pk>/pointer/', views.booking_mark, name='booking_mark'),

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
