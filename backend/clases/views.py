from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from datetime import datetime, timedelta, time as dtime
from django.db.models import Q
from django.utils.timezone import now, make_aware, get_current_timezone, localdate
from django.contrib import messages
from usuarios.models import Usuario
from .models import Clase
from director.models import EstadoInstructor  # activos del director
from backend_project.utils import centro_del_sesion


def _parse_fecha(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return localdate()  # SIEMPRE fecha local por defecto


def clases_del_dia(request):
    """
    Boletería: muestra solo los instructores ACTIVOS en la fecha seleccionada.
    Sin checkbox de 'solo activos'. Navegación de días con botones.
    """
    # 1) Fecha (por defecto: local)
    fecha_str = request.GET.get("fecha")
    fecha = _parse_fecha(fecha_str) if fecha_str else localdate()

    # 2) Instructores activos ese día (si no hay estado cargado, no muestra nadie)
    activos_ids = list(
        EstadoInstructor.objects
        .filter(fecha=fecha, activo=True)
        .values_list("instructor__rut_usuario", flat=True)
    )

    instructores = (
        Usuario.objects.filter(
            tipo_de_usuario__tipo_de_usuario__iexact="Instructor",
            rut_usuario__in=activos_ids if activos_ids else ["__NONE__"],
        )
        .order_by("apellido", "nombre")
    )

    # 3) Slots 30 min (09-17)
    HORAS = []
    start_dt = datetime.strptime(f"{fecha} 09:00", "%Y-%m-%d %H:%M")
    end_dt   = datetime.strptime(f"{fecha} 17:00", "%Y-%m-%d %H:%M")
    cur = start_dt
    while cur <= end_dt:
        HORAS.append(cur.strftime("%H:%M"))
        cur += timedelta(minutes=30)

    # 4) Clases del día
    clases_hoy = (
        Clase.objects.filter(hora_inicio__date=fecha)
        .select_related("rut_usuario")
        .order_by("hora_inicio")
    )

    # 5) Grilla
    horario = {inst.rut_usuario: {slot: None for slot in HORAS} for inst in instructores}
    tz = get_current_timezone()

    for clase in clases_hoy:
        inst_id = clase.rut_usuario.rut_usuario
        if inst_id not in horario:
            continue  # si el inst no está activo/no se muestra
        inicio, fin = clase.hora_inicio, clase.hora_fin
        for slot_str in HORAS:
            slot_naive = datetime.strptime(f"{fecha} {slot_str}", "%Y-%m-%d %H:%M")
            slot_inicio = make_aware(slot_naive, timezone=tz)
            slot_fin = slot_inicio + timedelta(minutes=30)
            if (slot_inicio < fin) and (slot_fin > inicio):
                horario[inst_id][slot_str] = clase

    filas_tabla = []
    for inst in instructores:
        celdas = []
        for slot in HORAS:
            celdas.append({
                "hora": slot,
                "clase": horario[inst.rut_usuario][slot],
        })
        filas_tabla.append({
            "instructor": inst,
            "activo": True,  # ya están filtrados por activos
            "celdas": celdas,
        })

        context = {
            "fecha": fecha,
            "horas": HORAS,
            "filas_tabla": filas_tabla,
            "error_crear": request.session.pop("error_crear", None),
        }
        return render(request, "clases/clases_del_dia.html", context)


def _render_error(request, msg, fecha=None):
    request.session["error_crear"] = msg
    if fecha:
        return redirect(f"{reverse('clases_del_dia')}?fecha={fecha.strftime('%Y-%m-%d')}")
    return redirect("clases_del_dia")


def crear_clase(request):
    if request.method != "POST":
        return _render_error(request, "Método no permitido.")

    # Fecha que está viendo boletería (viene del hidden del modal)
    fecha_str = request.POST.get("fecha")
    dia_obj = _parse_fecha(fecha_str)

    try:
        disciplina = request.POST["disciplina_clase"]
        nombre_titular = request.POST["nombre_titular"]
        titular_telefono = request.POST["titular_telefono"]
        nivel_clase = int(request.POST["nivel_clase"])
        hora_sola = request.POST["hora_sola"]              # "HH:MM"
        duracion = int(request.POST["duracion"])
        cantidad_alumnos = int(request.POST["cantidad_alumnos"])
        rut_usuario = request.POST["rut_usuario"]
    except KeyError:
        return _render_error(request, "Faltan campos obligatorios.", dia_obj)
    except ValueError:
        return _render_error(request, "Formato inválido en nivel/duración/alumnos.", dia_obj)

    # Convertir "HH:MM" a aware en la TZ del proyecto, usando la FECHA elegida
    tz = get_current_timezone()
    try:
        hh, mm = map(int, hora_sola.split(":"))
    except Exception:
        return _render_error(request, "Hora inválida.", dia_obj)

    inicio_local_naive = datetime.combine(dia_obj, dtime(hh, mm))
    hora_inicio = make_aware(inicio_local_naive, timezone=tz)
    hora_fin = hora_inicio + timedelta(minutes=duracion)

    # Validar instructor
    try:
        instructor = Usuario.objects.get(rut_usuario=rut_usuario)
    except Usuario.DoesNotExist:
        return _render_error(request, "Instructor no encontrado.", dia_obj)

    # Debe estar activo ese día
    if not EstadoInstructor.objects.filter(
        fecha=dia_obj, instructor=instructor, activo=True
    ).exists():
        return _render_error(request, f"El instructor {instructor.nombre} no está activo ese día.", dia_obj)

    # Validar solape
    if Clase.objects.filter(
        rut_usuario=instructor,
        hora_inicio__lt=hora_fin,
        hora_fin__gt=hora_inicio,
    ).exists():
        return _render_error(request, "Ese instructor ya tiene una clase en ese horario.", dia_obj)

    # Crear
    Clase.objects.create(
        nombre_titular=nombre_titular,
        titular_telefono=titular_telefono,
        nivel_clase=nivel_clase,
        disciplina_clase=disciplina,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        duracion=duracion,
        cantidad_alumnos=cantidad_alumnos,
        rut_usuario=instructor,
    )
    messages.success(request, "Clase creada correctamente.")
    return redirect(f"{reverse('clases_del_dia')}?fecha={dia_obj.strftime('%Y-%m-%d')}")


def editar_clase(request, id_clase):
    clase = get_object_or_404(Clase, id_clase=id_clase)
    if request.method != "POST":
        return redirect(f"{reverse('clases_del_dia')}?fecha={clase.hora_inicio.date().strftime('%Y-%m-%d')}")

    nuevo_nombre = request.POST.get("nombre_titular", clase.nombre_titular)
    nuevo_tel = request.POST.get("titular_telefono", clase.titular_telefono)
    nuevo_nivel = int(request.POST.get("nivel_clase", clase.nivel_clase))
    nuevo_alumnos = int(request.POST.get("cantidad_alumnos", clase.cantidad_alumnos))
    nueva_duracion = int(request.POST.get("duracion", clase.duracion))
    nuevo_instructor = request.POST.get("rut_usuario", clase.rut_usuario_id)

    fecha_clase = clase.hora_inicio.date()
    nuevo_hora_inicio = clase.hora_inicio
    nuevo_hora_fin = nuevo_hora_inicio + timedelta(minutes=nueva_duracion)

    choque = (
        Clase.objects
        .filter(
            rut_usuario_id=nuevo_instructor,
            hora_inicio__lt=nuevo_hora_fin,
            hora_fin__gt=nuevo_hora_inicio,
        )
        .exclude(pk=clase.pk)
        .exists()
    )
    if choque:
        return _render_error(request, "Ese instructor ya tiene una clase en ese horario.", fecha_clase)

    if not EstadoInstructor.objects.filter(
        fecha=fecha_clase, instructor__rut_usuario=nuevo_instructor, activo=True
    ).exists():
        return _render_error(request, "El instructor seleccionado no está activo ese día.", fecha_clase)

    clase.nombre_titular = nuevo_nombre
    clase.titular_telefono = nuevo_tel
    clase.nivel_clase = nuevo_nivel
    clase.cantidad_alumnos = nuevo_alumnos
    clase.duracion = nueva_duracion
    clase.hora_fin = nuevo_hora_fin
    clase.rut_usuario_id = nuevo_instructor
    clase.save()

    return redirect(f"{reverse('clases_del_dia')}?fecha={fecha_clase.strftime('%Y-%m-%d')}")


def eliminar_clase(request, id_clase):
    clase = get_object_or_404(Clase, id_clase=id_clase)
    fecha = clase.hora_inicio.date()
    if request.method == "POST":
        clase.delete()
    return redirect(f"{reverse('clases_del_dia')}?fecha={fecha.strftime('%Y-%m-%d')}")
