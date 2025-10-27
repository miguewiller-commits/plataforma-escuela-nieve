from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime, timedelta
from django.db.models import Q
from django.utils.timezone import now, make_aware, get_current_timezone

from usuarios.models import Usuario
from .models import Clase
from django.utils.timezone import localdate


def crear_clase(request):
    if request.method == "POST":
        nombre_titular = request.POST.get("nombre_titular")
        titular_telefono = request.POST.get("titular_telefono")
        disciplina_clase = request.POST.get("disciplina_clase")
        nivel_clase = request.POST.get("nivel_clase")
        hora_sola = request.POST.get("hora_sola")
        duracion = request.POST.get("duracion")
        cantidad_alumnos = request.POST.get("cantidad_alumnos")
        rut_usuario = request.POST.get("rut_usuario")

        # validar campos obligatorios
        if not (nombre_titular and titular_telefono and disciplina_clase and nivel_clase
                and hora_sola and duracion and cantidad_alumnos and rut_usuario):
            # volvemos al día con error
            return _render_error_clase_existente(
                request,
                "Faltan datos para crear la clase."
            )

        nivel_clase = int(nivel_clase)
        duracion = int(duracion)
        cantidad_alumnos = int(cantidad_alumnos)

        # construir inicio/fin reales (hoy + hora_sola + duracion)
        hoy_fecha = now().date()
        hora_inicio_str = f"{hoy_fecha} {hora_sola}"  # ej "2025-10-26 15:30"
        hora_inicio = datetime.strptime(hora_inicio_str, "%Y-%m-%d %H:%M")
        hora_fin = hora_inicio + timedelta(minutes=duracion)

        # === VALIDACIÓN DE SOLAPE ===
        # ¿Ese instructor tiene una clase que se cruce con este rango?
        choque = Clase.objects.filter(
            rut_usuario_id=rut_usuario,
            hora_inicio__lt=hora_fin,
            hora_fin__gt=hora_inicio,
        ).exists()

        if choque:
            return _render_error_clase_existente(
                request,
                "Ese instructor ya tiene una clase en ese horario."
            )

        # si NO hay choque -> crear
        Clase.objects.create(
            nombre_titular=nombre_titular,
            titular_telefono=titular_telefono,
            disciplina_clase=disciplina_clase,
            nivel_clase=nivel_clase,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            duracion=duracion,
            cantidad_alumnos=cantidad_alumnos,
            rut_usuario_id=rut_usuario,
        )

        return redirect("clases_del_dia")

    # si GET, no lo usamos acá en el modal
    # pero si sigues usando /clases/crear/ como pantalla aparte, puedes dejar tu render original
    # acá solo devolvemos algo neutro por seguridad
    return redirect("clases_del_dia")


def _render_error_clase_existente(request, mensaje):
    """
    Esta función vuelve a la vista del día con un mensaje de error
    para mostrarle a boletería que NO se pudo crear por conflicto.
    """
    # volvemos a pintar clases_del_dia con el mensaje
    # básicamente volvemos a ejecutar el código de clases_del_dia aquí dentro
    # para no duplicar lógica podrías importarla, pero lo simple es redirigir con un flag
    # versión simple: guardamos el mensaje en la sesión y redirigimos
    request.session["error_crear"] = mensaje
    return redirect("clases_del_dia")

def editar_clase(request, id_clase):
    clase = get_object_or_404(Clase, id_clase=id_clase)

    if request.method == "POST":
        # 1. Leemos lo nuevo del form
        nuevo_nombre = request.POST.get("nombre_titular", clase.nombre_titular)
        nuevo_tel = request.POST.get("titular_telefono", clase.titular_telefono)
        nuevo_nivel = request.POST.get("nivel_clase", clase.nivel_clase)
        nuevo_alumnos = request.POST.get("cantidad_alumnos", clase.cantidad_alumnos)
        nueva_duracion = request.POST.get("duracion", clase.duracion)
        nuevo_instructor = request.POST.get("rut_usuario", clase.rut_usuario_id)

        # asegurar ints
        try:
            nueva_duracion_int = int(nueva_duracion)
        except:
            nueva_duracion_int = clase.duracion

        # 2. Calculamos nuevo hora_fin (hora_inicio no cambia en este modal)
        nuevo_hora_inicio = clase.hora_inicio
        nuevo_hora_fin = clase.hora_inicio + timedelta(minutes=nueva_duracion_int)

        # 3. Validación de solape:
        # buscamos si el nuevo instructor ya tiene otra clase que se cruce
        # IMPORTANTE: excluimos esta misma clase con .exclude(pk=clase.pk)
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
            # guardamos mensaje de error en sesión y volvemos al tablero
            request.session["error_crear"] = (
                "Ese instructor ya tiene una clase en ese horario."
            )
            return redirect("clases_del_dia")

        # 4. Si no hay choque, guardamos los cambios
        clase.nombre_titular = nuevo_nombre
        clase.titular_telefono = nuevo_tel
        clase.nivel_clase = nuevo_nivel
        clase.cantidad_alumnos = nuevo_alumnos
        clase.duracion = nueva_duracion_int
        clase.hora_fin = nuevo_hora_fin
        clase.rut_usuario_id = nuevo_instructor

        clase.save()

    return redirect("clases_del_dia")

    # si alguien entra por GET directo tipo /clases/editar/5/ lo mandamos al tablero
    return redirect("clases_del_dia")

def eliminar_clase(request, id_clase):
    clase = get_object_or_404(Clase, id_clase=id_clase)

    if request.method == "POST":
        clase.delete()
        return redirect("clases_del_dia")

    return redirect("clases_del_dia")


def clases_del_dia(request):
    hoy = now().date()

    clases_hoy = (
        Clase.objects
        .filter(hora_inicio__date=hoy)
        .select_related("rut_usuario")
        .order_by("hora_inicio")
    )

    instructores = Usuario.objects.filter(
        tipo_de_usuario__tipo_de_usuario__iexact="Instructor"
    ).order_by("apellido", "nombre")

    # slots de 30 min entre 09:00 y 17:00
    start_hour = 9
    end_hour = 17

    HORAS = []
    start_dt = datetime.strptime(f"{hoy} {start_hour:02d}:00", "%Y-%m-%d %H:%M")
    end_dt   = datetime.strptime(f"{hoy} {end_hour:02d}:00", "%Y-%m-%d %H:%M")

    cur = start_dt
    while cur <= end_dt:
        HORAS.append(cur.strftime("%H:%M"))
        cur += timedelta(minutes=30)

    # mapa vacío: horario[instructor_rut][slot] = None
    horario = {}
    for inst in instructores:
        horario[inst.rut_usuario] = {slot: None for slot in HORAS}

    tz = get_current_timezone()

    # marcamos cada bloque ocupado si se solapa
    for clase in clases_hoy:
        inst_id = clase.rut_usuario.rut_usuario
        inicio = clase.hora_inicio  # aware
        fin = clase.hora_fin        # aware

        for slot_str in HORAS:
            slot_naive = datetime.strptime(f"{hoy} {slot_str}", "%Y-%m-%d %H:%M")
            slot_inicio = make_aware(slot_naive, timezone=tz)
            slot_fin = slot_inicio + timedelta(minutes=30)

            se_solapa = (slot_inicio < fin) and (slot_fin > inicio)
            if se_solapa:
                horario[inst_id][slot_str] = clase

    # convertimos a filas renderizables
    filas_tabla = []
    for inst in instructores:
        fila = {
            "instructor": inst,
            "celdas": []
        }
        for slot in HORAS:
            fila["celdas"].append(horario[inst.rut_usuario][slot])
        filas_tabla.append(fila)

    error_crear = request.session.pop("error_crear", None)

    context = {
        "fecha": hoy,
        "horas": HORAS,
        "filas_tabla": filas_tabla,
        "error_crear": error_crear,
    }

    return render(request, "clases/clases_del_dia.html", context)


    return render(request, "clases/clases_del_dia.html", context)