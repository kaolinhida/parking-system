from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('create-parking-grid/', views.create_parking_grid, name='create_parking_grid'),

    path('parkings/', views.dashboard_parking_list, name='parking_list'),
    path('parkings/<int:parking_id>/spaces/', views.dashboard_parking_spaces, name='parking_spaces'),
    path('spaces/<int:space_id>/edit/', views.dashboard_space_edit, name='space_edit'),
]