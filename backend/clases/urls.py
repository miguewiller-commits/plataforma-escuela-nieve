from django.urls import path
from . import views

urlpatterns = [
    path("crear/", views.crear_clase, name="crear_clase"),
    path("del_dia/", views.clases_del_dia, name="clases_del_dia"),
    path("editar/<int:id_clase>/", views.editar_clase, name="editar_clase"),
    path("eliminar/<int:id_clase>/", views.eliminar_clase, name="eliminar_clase"),
]
