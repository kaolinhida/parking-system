from django.urls import path

from . import views

app_name = 'reservations'

urlpatterns = [
    path('create/<int:space_id>/', views.create_reservation, name='create_reservation'),
]