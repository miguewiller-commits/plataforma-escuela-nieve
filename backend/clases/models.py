from django.db import models
from usuarios.models import Usuario

class Clase(models.Model):
    id_clase = models.AutoField(primary_key=True)

    nombre_titular = models.CharField(max_length=100)
    titular_telefono = models.CharField(max_length=30)

    nivel_clase = models.IntegerField()  # 1,2,3
    disciplina_clase = models.CharField(
        max_length=20,
        choices=[("ski", "Ski"), ("snow", "Snow")]
    )

    hora_inicio = models.DateTimeField()
    hora_fin = models.DateTimeField()
    duracion = models.IntegerField()  # en minutos

    cantidad_alumnos = models.IntegerField()

    # Instructor asignado a esta clase
    rut_usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        db_column="Rut_Usuario",
        related_name="clases_asignadas"
    )

    def __str__(self):
        return f"Clase {self.id_clase} - {self.disciplina_clase} nivel {self.nivel_clase}"
