from django.shortcuts import render

# Create your views here.
from datetime import datetime
from django.utils.timezone import now
from django.contrib.auth.hashers import check_password
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from usuarios.models import Usuario
from clases.models import Clase
from .serializers import UsuarioSerializer, ClaseSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def api_login(request):
    correo = request.data.get("correo")
    password = request.data.get("password")

    if not correo or not password:
        return Response(
            {"detail": "Correo y contraseña son obligatorios."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        usuario = Usuario.objects.get(correo=correo)
    except Usuario.DoesNotExist:
        return Response(
            {"detail": "Credenciales inválidas."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not check_password(password, usuario.contraseña):
        return Response(
            {"detail": "Credenciales inválidas."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Token de DRF (uno por usuario)
    token, _ = Token.objects.get_or_create(user=usuario)

    data_usuario = UsuarioSerializer(usuario).data

    return Response(
        {
            "token": token.key,
            "usuario": data_usuario,
        }
    )

from django.utils.timezone import now
from datetime import datetime

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_clases_instructor(request):
    """
    Devuelve las clases del instructor logueado para una fecha dada.
    Si no se envía fecha, se usa hoy.
    """
    fecha_str = request.GET.get("fecha")
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except Exception:
            return Response(
                {"detail": "Formato de fecha inválido. Usa YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:
        fecha = now().date()

    # Asumiendo que el usuario autenticado es tu Usuario
    usuario = request.user

    clases = (
        Clase.objects.filter(
            rut_usuario=usuario,
            hora_inicio__date=fecha,
        )
        .order_by("hora_inicio")
    )

    serializer = ClaseSerializer(clases, many=True)
    return Response(serializer.data)

from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import EmailTokenObtainPairSerializer

class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer

class MisClasesHoyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Devuelve las clases del instructor logueado para una fecha.
        Si no se manda ?fecha=YYYY-MM-DD, usa hoy.
        """
        fecha_str = request.GET.get("fecha")
        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({"detail": "Fecha inválida, use YYYY-MM-DD"}, status=400)
        else:
            fecha = datetime.today().date()

        # el instructor es el usuario logueado
        usuario = request.user

        clases = Clase.objects.filter(
            rut_usuario=usuario,
            hora_inicio__date=fecha
        ).order_by("hora_inicio")

        data = ClaseSerializer(clases, many=True).data
        return Response({
            "fecha": fecha.strftime("%Y-%m-%d"),
            "clases": data
        })