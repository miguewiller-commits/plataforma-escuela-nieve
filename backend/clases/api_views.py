from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.timezone import localdate
from .models import Clase
from datetime import datetime
from usuarios.models import Usuario
from django.core.exceptions import ObjectDoesNotExist

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def clases_instructor_dia(request):
    # 1. Fecha
    fecha_str = request.GET.get("fecha")
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"detail": "Formato de fecha inválido. Usa YYYY-MM-DD."},
                status=400,
            )
    else:
        fecha = localdate()

    # 2. Buscar instructor por correo = username del User
    user = request.user
    try:
        instructor = Usuario.objects.get(correo=user.username)
    except ObjectDoesNotExist:
        return Response(
            {"detail": "No se encontró un instructor con ese correo."},
            status=400,
        )

    # 3. Filtrar clases del día
    clases = (
        Clase.objects.filter(
            rut_usuario=instructor,
            hora_inicio__date=fecha,
        )
        .order_by("hora_inicio")
    )

    # 4. Armar JSON que usa Flutter
    data = []
    for c in clases:
        data.append(
            {
                "hora_inicio": c.hora_inicio.isoformat(),
                "hora_fin": c.hora_fin.isoformat(),
                "disciplina_clase": c.disciplina_clase,
                "nivel_clase": c.nivel_clase,
                "nombre_titular": c.nombre_titular,
                "titular_telefono": c.titular_telefono,
                "cantidad_alumnos": c.cantidad_alumnos,
            }
        )

    return Response(data)