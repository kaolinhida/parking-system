from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('create-parking-grid/', views.create_parking_grid, name='create_parking_grid'),
]