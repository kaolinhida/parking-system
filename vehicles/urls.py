from django.urls import path

from . import views

app_name = 'vehicles'

urlpatterns = [
    path('', views.vehicle_list, name='vehicle_list'),
    path('add/', views.vehicle_add, name='vehicle_add'),
    path('<int:vehicle_id>/edit/', views.vehicle_edit, name='vehicle_edit'),
    path('<int:vehicle_id>/deactivate/', views.vehicle_deactivate, name='vehicle_deactivate'),
]