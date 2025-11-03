from django.contrib import admin
from .models import EstadoInstructor

@admin.register(EstadoInstructor)
class EstadoInstructorAdmin(admin.ModelAdmin):
    list_display = ("fecha", "instructor", "activo")
    list_filter = ("fecha", "activo")
    search_fields = ("instructor__nombre", "instructor__apellido", "instructor__rut_usuario")
