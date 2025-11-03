from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.director_dashboard, name='director_dashboard'),
    path('asistencia/', views.director_asistencia, name='director_asistencia'),
    path('reportes/', views.director_reportes, name='director_reportes'),
    path('historial/', views.director_historial, name='director_historial'),
    path('instructores/crear/', views.director_crear_instructor, name='director_crear_instructor'),
    path('instructores/eliminar/<str:rut>/', views.director_eliminar_instructor, name='director_eliminar_instructor'),
]
