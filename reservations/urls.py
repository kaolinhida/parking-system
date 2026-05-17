from django.urls import path

from . import views

app_name = 'reservations'

urlpatterns = [
    path('create/<int:space_id>/', views.create_reservation, name='create_reservation'),
    path('cancel/<int:reservation_id>/', views.cancel_reservation, name='cancel_reservation'),

    path('qr/<int:reservation_id>/', views.reservation_qr_page, name='reservation_qr_page'),
    path('qr/<int:reservation_id>/image/', views.reservation_qr_image, name='reservation_qr_image'),
]