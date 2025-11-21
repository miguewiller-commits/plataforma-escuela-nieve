from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.timezone import localdate
from .models import Clase

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def clases_instructor_dia(request):
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        from datetime import datetime
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    else:
        fecha = localdate()

    usuario = request.user  # debe ser tu modelo Usuario
    clases = Clase.objects.filter(
        rut_usuario=usuario,
        hora_inicio__date=fecha,
    ).order_by('hora_inicio')

    data = []
    for c in clases:
      data.append({
        "hora_inicio": c.hora_inicio.strftime('%H:%M'),
        "hora_fin": c.hora_fin.strftime('%H:%M'),
        "disciplina": c.disciplina_clase,
        "nivel": c.nivel_clase,
        "nombre_titular": c.nombre_titular,
      })

    return Response(data)
