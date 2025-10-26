from django.db import models

class CentroDeEsqui(models.Model):
    id_centro = models.AutoField(primary_key=True)
    nombre_centro = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.nombre_centro} ({self.ubicacion})"
