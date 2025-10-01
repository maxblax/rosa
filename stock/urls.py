from django.urls import path
from . import views

app_name = 'stock'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='list'),
    path('create/', views.ProductCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ProductDeleteView.as_view(), name='delete'),
    path('<int:pk>/adjust/', views.adjust_quantity_view, name='adjust'),
]
