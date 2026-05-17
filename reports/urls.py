from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_home, name='home'),
    path('export/csv/', views.reports_export_csv, name='export_csv'),
]
