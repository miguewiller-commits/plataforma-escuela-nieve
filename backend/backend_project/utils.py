from usuarios.models import Usuario

def usuario_actual(request):
    rut = request.session.get('usuario_id')
    if not rut:
        return None
    try:
        return Usuario.objects.select_related('id_centro', 'tipo_de_usuario').get(rut_usuario=rut)
    except Usuario.DoesNotExist:
        return None

def centro_del_sesion(request):
    u = usuario_actual(request)
    return getattr(u, 'id_centro', None)