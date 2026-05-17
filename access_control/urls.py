from django.urls import path

from . import views

app_name = 'access_control'

urlpatterns = [
    path('', views.access_control_home, name='home'),
    path('reservation/<uuid:access_token>/', views.reservation_detail, name='reservation_detail'),
    path('reservation/<uuid:access_token>/check-in/', views.check_in, name='check_in'),
    path('reservation/<uuid:access_token>/check-out/', views.check_out, name='check_out'),
]