from django.shortcuts import render
from django.db.models import Sum, Count
from django.utils.timezone import now, get_current_timezone, make_aware
from datetime import timedelta, datetime, date
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
from django.utils.timezone import localdate
from django.contrib.auth.models import User




def _parse_fecha(value: str, default: date):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return default
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
# 🔹 REPORTES (por instructor / todos los instructores)
@role_required('jefe_centro', 'director')
@role_required('jefe_centro', 'director')
def director_reportes(request):
    """
    Reportes:
    - Si en el select de instructor se elige un RUT => modo 'uno' (detalle).
    - Si se elige 'todos' => modo 'todos' (resumen por instructor).
    """
    centro = centro_del_sesion(request)

    # --- Instructores disponibles (del centro) ---
    qs_instructores = Usuario.objects.filter(
        tipo_de_usuario__tipo_de_usuario__iexact="instructor"
    )
    if centro:
        qs_instructores = qs_instructores.filter(id_centro=centro)

    instructores = qs_instructores.order_by("apellido", "nombre")

    # --- Filtros GET ---
    inst_id = request.GET.get("inst")  # puede ser RUT, "todos" o None
    desde_str = request.GET.get("desde")
    hasta_str = request.GET.get("hasta")
    mes_str = request.GET.get("mes")  # opcional: viene desde el dashboard (YYYY-MM)

    hoy = localdate()

    # Si viene "mes=YYYY-MM" y no hay desde/hasta, usamos el mes completo
    if mes_str and not (desde_str or hasta_str):
        try:
            year, month = map(int, mes_str.split("-"))
            desde_default = date(year, month, 1)
        except Exception:
            desde_default = hoy.replace(day=1)
    else:
        desde_default = hoy.replace(day=1)

    # parse desde/hasta
    desde = _parse_fecha(desde_str, desde_default)
    if hasta_str:
        hasta = _parse_fecha(hasta_str, hoy)
    else:
        next_month = (desde.replace(day=28) + timedelta(days=4)).replace(day=1)
        hasta = next_month - timedelta(days=1)

    if desde > hasta:
        desde, hasta = hasta, desde

    # Determinar modo según valor de inst
    if inst_id == "todos":
        modo = "todos"
    else:
        modo = "uno"

    instructor_sel = None
    clases = []
    total_minutos = 0

    resumen = []
    total_minutos_global = 0

    # ================== MODO: POR INSTRUCTOR ==================
    if modo == "uno" and inst_id:
        filtros_instructor = {
            "rut_usuario": inst_id,
            "tipo_de_usuario__tipo_de_usuario__iexact": "instructor",
        }
        if centro:
            filtros_instructor["id_centro"] = centro

        instructor_sel = get_object_or_404(Usuario, **filtros_instructor)

        clases = (
            Clase.objects.filter(
                rut_usuario=instructor_sel,
                hora_inicio__date__gte=desde,
                hora_inicio__date__lte=hasta,
            )
            .order_by("hora_inicio")
        )

        agg = clases.aggregate(total=Sum("duracion"))
        total_minutos = agg["total"] or 0

    # ================== MODO: TODOS LOS INSTRUCTORES ==================
    elif modo == "todos":
        clases_qs = Clase.objects.filter(
            hora_inicio__date__gte=desde,
            hora_inicio__date__lte=hasta,
        )
        if centro:
            clases_qs = clases_qs.filter(rut_usuario__id_centro=centro)

        resumen_qs = (
            clases_qs
            .values(
                "rut_usuario__rut_usuario",
                "rut_usuario__nombre",
                "rut_usuario__apellido",
            )
            .annotate(
                total_minutos=Sum("duracion"),
                total_clases=Count("id_clase"),
            )
            .order_by("-total_minutos")
        )

        resumen = []
        for row in resumen_qs:
            mins = row["total_minutos"] or 0
            horas = round(mins / 60.0, 1) if mins else 0
            row["total_minutos_horas"] = horas
            resumen.append(row)
            total_minutos_global += mins

    total_horas = round(total_minutos / 60.0, 1) if total_minutos else 0
    total_horas_global = round(total_minutos_global / 60.0, 1) if total_minutos_global else 0

    context = {
        "instructores": instructores,
        "instructor_sel": instructor_sel,
        "clases": clases,
        "desde": desde,
        "hasta": hasta,
        "inst_id": inst_id,
        "total_minutos": total_minutos,
        "total_horas": total_horas,
        "modo": modo,
        "resumen": resumen,
        "total_minutos_global": total_minutos_global,
        "total_horas_global": total_horas_global,
    }
    return render(request, "director/reportes.html", context)




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
    Crea un instructor asignándolo automáticamente al centro del director
    Y TAMBIÉN crea/actualiza el auth.User para que pueda loguearse por /api/token/.
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
                # 1) Guardar tu modelo Usuario (ya asigna el centro)
                usuario = form.save(center=centro)

                # 2) Datos para el auth.User
                correo = (usuario.correo or "").strip().lower()
                rut = usuario.rut_usuario
                raw_password = form.cleaned_data.get("contraseña") or "cambiar123"

                # username = correo (si hay) o RUT
                username = correo or rut

                # 3) Crear o actualizar el auth.User
                user, created = User.objects.get_or_create(username=username)
                user.first_name = usuario.nombre
                user.last_name = usuario.apellido
                if correo:
                    user.email = correo
                user.is_active = True
                user.set_password(raw_password)
                user.save()

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
    Elimina instructor del mismo centro (modelo Usuario)
    Y también elimina el auth.User asociado (username = correo o rut).
    Preserva ?fecha y ?solo_activos.
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

    # Si tiene clases, no lo dejamos borrar (igual que antes)
    if Clase.objects.filter(rut_usuario=inst).exists():
        messages.error(request, "No se puede eliminar: el instructor tiene clases registradas.")
        return redirect(_redir_dashboard(fecha, solo_activos))

    # 🔹 Borrar también el auth.User asociado
    username_candidates = []
    if inst.correo:
        username_candidates.append(inst.correo.strip().lower())
    username_candidates.append(inst.rut_usuario)

    User.objects.filter(username__in=username_candidates).delete()

    # 🔹 Borrar el registro de Usuario
    inst.delete()

    messages.success(request, "Instructor eliminado (y usuario de acceso eliminado).")
    return redirect(_redir_dashboard(fecha, solo_activos))
