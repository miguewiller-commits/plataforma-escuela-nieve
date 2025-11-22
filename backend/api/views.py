from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken

from usuarios.models import Usuario


class InstructorLoginView(APIView):
    # esta clase es la que estás importando en urls.py
    permission_classes = [AllowAny]
    authentication_classes = []  # no exige JWT para entrar

    def post(self, request):
        correo = request.data.get("correo")
        password = request.data.get("password")

        if not correo or not password:
            return Response(
                {"detail": "correo y password son obligatorios"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # buscar en tu tabla usuarios_usuario
        try:
            instructor = Usuario.objects.get(correo=correo)
        except Usuario.DoesNotExist:
            return Response(
                {"detail": "Credenciales inválidas"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # comparar con la contraseña encriptada
        if not check_password(password, instructor.contraseña):
            return Response(
                {"detail": "Credenciales inválidas"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # crear o reutilizar User de Django vinculado
        if getattr(instructor, "user", None) is None:
            user = User.objects.create(
                username=correo,
                email=correo,
                is_active=True,
            )
            user.password = instructor.contraseña  # ya viene encriptada
            user.save()
            # si aún no tienes el campo user en tu modelo Usuario,
            # este bloque lo ajustamos después
            if hasattr(instructor, "user"):
                instructor.user = user
                instructor.save(update_fields=["user"])
        else:
            user = instructor.user

        # generar tokens JWT
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )
