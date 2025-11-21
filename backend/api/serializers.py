from rest_framework import serializers
from usuarios.models import Usuario
from clases.models import Clase

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            "rut_usuario",
            "nombre",
            "apellido",
            "correo",
            "numero_telefono",
            "tipo_de_usuario",
            "disciplina",
            "nivel_instructor",
            "idioma",
        ]

class ClaseSerializer(serializers.ModelSerializer):
    instructor_nombre = serializers.CharField(source="rut_usuario.nombre", read_only=True)
    instructor_apellido = serializers.CharField(source="rut_usuario.apellido", read_only=True)

    class Meta:
        model = Clase
        fields = [
            "id_clase",
            "disciplina_clase",
            "nivel_clase",
            "hora_inicio",
            "hora_fin",
            "duracion",
            "cantidad_alumnos",
            "nombre_titular",
            "titular_telefono",
            "instructor_nombre",
            "instructor_apellido",
        ]

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from usuarios.models import Usuario

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    # renombramos el campo para que Flutter mande "email" en lugar de "username"
    email = serializers.EmailField(write_only=True)

    def validate(self, attrs):
        # copiamos el email al campo username que SimpleJWT espera
        email = attrs.get("email")
        if email:
            attrs["username"] = email
        return super().validate(attrs)
