from django.urls import path

from . import views

app_name = 'parkings'

urlpatterns = [
    path('', views.parking_list, name='parking_list'),
    path('search/', views.parking_global_search, name='global_search'),
    path('<int:parking_id>/', views.parking_detail, name='parking_detail'),
]