# director/models.py
from django.db import models
from usuarios.models import Usuario

class EstadoInstructor(models.Model):
    instructor = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="estados_diarios",   # <— deja el related_name si lo quieres
    )
    fecha = models.DateField(db_index=True)
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = (("instructor", "fecha"),)
        indexes = [models.Index(fields=["instructor", "fecha"])]

    def __str__(self):
        return f"{self.instructor} — {'Activo' if self.activo else 'Inactivo'} — {self.fecha}"
