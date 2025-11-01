from django.db import models
from centros.models import CentroDeEsqui

class Identificador(models.Model):
    # Ej: "Instructor", "Boleteria", "Jefe_De_Centro"
    tipo_de_usuario = models.CharField(primary_key=True, max_length=30)

    def __str__(self):
        return self.tipo_de_usuario

class Usuario(models.Model):
    # RUT será la PK
    rut_usuario = models.CharField(primary_key=True, max_length=20)

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    edad = models.IntegerField(null=True, blank=True)

    # Para instructores
    disciplina = models.CharField(
        max_length=20,
        choices=[("ski", "Ski"), ("snow", "Snow"), ("ambos", "Ambos")],
        null=True,
        blank=True
    )
    nivel_instructor = models.IntegerField(
        null=True,
        blank=True
    )  # 1,2,3

    # Contacto personal
    numero_telefono = models.CharField(max_length=30, null=True, blank=True)
    correo = models.EmailField(null=True, blank=True)
    contraseña = models.CharField(max_length=255)

    # Idiomas que habla el instructor (texto libre tipo "español, inglés, portugués")
    idioma = models.CharField(max_length=200, null=True, blank=True)

    # Relación al tipo de usuario
    tipo_de_usuario = models.ForeignKey(
        Identificador,
        on_delete=models.PROTECT,  # no quiero que se borre el tipo y deje usuarios colgando
        db_column="Tipo_De_Usuario"
    )

    # Relación al centro
    id_centro = models.ForeignKey(
        CentroDeEsqui,
        on_delete=models.PROTECT,
        db_column="Id_Centro",
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.rut_usuario})"

