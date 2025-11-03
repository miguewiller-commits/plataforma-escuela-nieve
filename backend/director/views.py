from django.shortcuts import render
from django.db.models import Sum, Count
from django.utils.timezone import now, get_current_timezone, make_aware
from datetime import timedelta, datetime
from clases.models import Clase
from usuarios.models import Usuario
from .models import EstadoInstructor
from .decorators import role_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import InstructorForm
from django.shortcuts import render
from django.contrib import messages
from backend_project.utils import centro_del_sesion
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse


# 🔹 DASHBOARD: vista principal del director
@role_required('director', 'jefe_centro')
def director_dashboard(request):
    """
    Muestra el calendario diario con instructores activos/inactivos.
    Permite navegar por fechas (?fecha=YYYY-MM-DD) y filtrar solo activos (?solo_activos=1).
    """
    # 1️⃣ Fecha seleccionada
    try:
        fecha_str = request.GET.get("fecha")
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else now().date()
    except Exception:
        fecha = now().date()

    solo_activos = request.GET.get("solo_activos") == "1"

    # 2️⃣ Instructores base
    centro = centro_del_sesion(request)

    instructores_qs = Usuario.objects.filter(
        tipo_de_usuario__tipo_de_usuario__iexact="instructor",
        id_centro=centro
    ).order_by("apellido", "nombre")

    estados_qs = EstadoInstructor.objects.filter(fecha=fecha, instructor__id_centro=centro)


    # 3️⃣ Estado activo/inactivo del día
    estados_qs = EstadoInstructor.objects.filter(fecha=fecha)
    estados_map = {e.instructor.rut_usuario: e.activo for e in estados_qs}

    if solo_activos:
        activos_rut = [rut for rut, act in estados_map.items() if act]
        if activos_rut:
            instructores_qs = instructores_qs.filter(rut_usuario__in=activos_rut)

    # 4️⃣ Horarios de 30 minutos (9:00 a 17:00)
    start_hour, end_hour = 9, 17
    HORAS = []
    cur = datetime.strptime(f"{fecha} {start_hour:02d}:00", "%Y-%m-%d %H:%M")
    limit = datetime.strptime(f"{fecha} {end_hour:02d}:00", "%Y-%m-%d %H:%M")
    while cur <= limit:
        HORAS.append(cur.strftime("%H:%M"))
        cur += timedelta(minutes=30)

    # 5️⃣ Clases del día
    clases_hoy = (
        Clase.objects
        .filter(hora_inicio__date=fecha)
        .select_related("rut_usuario")
        .order_by("hora_inicio")
    )

    # 6️⃣ Mapa horario vacío
    horario = {inst.rut_usuario: {slot: None for slot in HORAS} for inst in instructores_qs}
    tz = get_current_timezone()

    # 7️⃣ Rellenar celdas
    for clase in clases_hoy:
        inst_id = clase.rut_usuario.rut_usuario
        inicio, fin = clase.hora_inicio, clase.hora_fin
        if inst_id not in horario:
            continue
        for slot_str in HORAS:
            slot_naive = datetime.strptime(f"{fecha} {slot_str}", "%Y-%m-%d %H:%M")
            slot_inicio = make_aware(slot_naive, timezone=tz)
            slot_fin = slot_inicio + timedelta(minutes=30)
            if (slot_inicio < fin) and (slot_fin > inicio):
                horario[inst_id][slot_str] = clase

    # 8️⃣ Filas renderizables
    filas_tabla = []
    for inst in instructores_qs:
        fila = {
            "instructor": inst,
            "activo": estados_map.get(inst.rut_usuario, False),
            "celdas": [horario[inst.rut_usuario][slot] for slot in HORAS],
        }
        filas_tabla.append(fila)

    # 9️⃣ Resumen simple
    minutos_totales = clases_hoy.aggregate(m=Sum("duracion"))["m"] or 0
    horas_totales = round(minutos_totales / 60.0, 2)

    context = {
        "fecha": fecha,
        "horas": HORAS,
        "filas_tabla": filas_tabla,
        "solo_activos": solo_activos,
        "resumen_horas": horas_totales,
    }
    return render(request, "director/dashboard.html", context)


# 🔹 ASISTENCIA DIARIA (toggle activo/inactivo)
@role_required('director', 'jefe_centro')
@require_POST
def director_asistencia(request):
    """
    Guarda asistencia del día (activo/inactivo por instructor) y retorna JSON.
    Espera:
      - fecha: YYYY-MM-DD
      - activos: lista de ruts activos
    """
    fecha_str = request.POST.get("fecha")
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else now().date()
    except Exception:
        fecha = now().date()

    activos = set(request.POST.getlist("activos"))  # lista de ruts activos

    instructores = Usuario.objects.filter(
        tipo_de_usuario__tipo_de_usuario__iexact="instructor"
    )

    for inst in instructores:
        activo = inst.rut_usuario in activos
        EstadoInstructor.objects.update_or_create(
            instructor=inst, fecha=fecha, defaults={"activo": activo}
        )

    return JsonResponse({"ok": True})


# 🔹 REPORTES MENSUALES
@role_required('jefe_centro', 'director')
def director_reportes(request):
    mes = request.GET.get("mes") or now().strftime("%Y-%m")
    year, month = map(int, mes.split("-"))

    clases_mes = Clase.objects.filter(
        hora_inicio__year=year,
        hora_inicio__month=month
    )

    resumen_min = (
        clases_mes
        .values("rut_usuario__rut_usuario", "rut_usuario__nombre", "rut_usuario__apellido")
        .annotate(minutos_totales=Sum("duracion"), cantidad_clases=Count("id_clase"))
        .order_by("-minutos_totales")
    )

    resumen = []
    for r in resumen_min:
        horas = round((r["minutos_totales"] or 0) / 60.0, 2)
        resumen.append({
            "rut": r["rut_usuario__rut_usuario"],
            "nombre": r["rut_usuario__nombre"],
            "apellido": r["rut_usuario__apellido"],
            "horas_totales": horas,
            "cantidad_clases": r["cantidad_clases"],
        })

    return render(request, "director/reportes.html", {"resumen": resumen, "mes": mes})


# 🔹 HISTORIAL DE CLASES
@role_required('jefe_centro', 'director')
def director_historial(request):
    fecha_inicio = request.GET.get("desde")
    fecha_fin = request.GET.get("hasta")

    clases = Clase.objects.all()
    if fecha_inicio and fecha_fin:
        clases = clases.filter(hora_inicio__date__range=[fecha_inicio, fecha_fin])

    instructor = request.GET.get("instructor")
    if instructor:
        clases = clases.filter(rut_usuario_id=instructor)

    instructores = Usuario.objects.filter(
        tipo_de_usuario__tipo_de_usuario__iexact="instructor"
    )

    return render(request, "director/historial.html", {
        "clases": clases.order_by("-hora_inicio"),
        "instructores": instructores,
    })

@role_required('director', 'jefe_centro')
def instructores_list(request):
    centro = centro_del_sesion(request)
    qs = Usuario.objects.filter(
        tipo_de_usuario__tipo_de_usuario__iexact="instructor",
        id_centro=centro
    ).order_by("apellido", "nombre")

    # Form vacío para el modal de "Crear"
    form = InstructorForm()

    return render(
        request,
        "director/instructores_list.html",
        {"instructores": qs, "form": form}
    )

def _redir_dashboard(fecha=None, solo_activos=None):
    url = reverse('director_dashboard')
    params = []
    if fecha:
        params.append(f"fecha={fecha}")
    if solo_activos in ("1", 1, True, "true", "True"):
        params.append("solo_activos=1")
    if params:
        url = f"{url}?{'&'.join(params)}"
    return url

@role_required('director', 'jefe_centro')
def director_crear_instructor(request):
    """
    Crea un instructor asignándolo automáticamente al centro del director.
    Preserva ?fecha y ?solo_activos al volver al dashboard.
    """
    # valores de navegación para preservar
    fecha = request.POST.get("fecha") or request.GET.get("fecha")
    solo_activos = request.POST.get("solo_activos") or request.GET.get("solo_activos")

    if request.method == 'POST':
        centro = centro_del_sesion(request)
        if not centro:
            messages.error(request, "No se pudo determinar tu centro.")
            return redirect(_redir_dashboard(fecha, solo_activos))

        form = InstructorForm(request.POST)
        if form.is_valid():
            try:
                form.save(center=centro)  # <-- asigna mismo centro del director
                messages.success(request, "Instructor creado correctamente.")
            except Exception as e:
                messages.error(request, f"No se pudo crear: {e}")
        else:
            messages.error(request, "Formulario inválido. Revisa los campos.")

        return redirect(_redir_dashboard(fecha, solo_activos))

    # si GET directo:
    return redirect(_redir_dashboard(fecha, solo_activos))


@role_required('director', 'jefe_centro')
@require_POST
def director_eliminar_instructor(request, rut):
    """
    Elimina instructor del mismo centro. Preserva ?fecha y ?solo_activos.
    """
    fecha = request.POST.get("fecha") or request.GET.get("fecha")
    solo_activos = request.POST.get("solo_activos") or request.GET.get("solo_activos")

    centro = centro_del_sesion(request)
    if not centro:
        messages.error(request, "No se pudo determinar tu centro.")
        return redirect(_redir_dashboard(fecha, solo_activos))

    try:
        inst = Usuario.objects.get(
            rut_usuario=rut,
            tipo_de_usuario__tipo_de_usuario__iexact='instructor',
            id_centro=centro
        )
    except Usuario.DoesNotExist:
        messages.error(request, "Instructor no encontrado en tu centro.")
        return redirect(_redir_dashboard(fecha, solo_activos))

    if Clase.objects.filter(rut_usuario=inst).exists():
        messages.error(request, "No se puede eliminar: el instructor tiene clases registradas.")
        return redirect(_redir_dashboard(fecha, solo_activos))

    inst.delete()
    messages.success(request, "Instructor eliminado.")
    return redirect(_redir_dashboard(fecha, solo_activos))