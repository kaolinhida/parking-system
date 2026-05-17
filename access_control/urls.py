from django.urls import path

from . import views

app_name = 'access_control'

urlpatterns = [
    path('', views.access_control_home, name='home'),
    path('logs/', views.access_logs, name='logs'),

    path('reservation/<uuid:access_token>/', views.reservation_detail, name='reservation_detail'),
    path('reservation/<uuid:access_token>/check-in/', views.check_in, name='check_in'),
    path('reservation/<uuid:access_token>/check-out/', views.check_out, name='check_out'),
    path('reservation/<uuid:access_token>/mark-paid/', views.mark_paid, name='mark_paid'),
    path('reservation/<uuid:access_token>/mark-overtime-paid/', views.mark_overtime_paid, name='mark_overtime_paid'),
]
