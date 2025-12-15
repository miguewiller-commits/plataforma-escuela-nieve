from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils.timezone import localdate
from datetime import datetime

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# Asegúrate de importar tus modelos y forms correctamente
from usuarios.models import Usuario, Identificador
from clases.models import Clase
from director.models import EstadoInstructor
from .forms import LoginForm, RegistroForm
from api.serializers import UsuarioSerializer, ClaseSerializer

# --- VISTAS DE AUTENTICACIÓN ---

def login_view(request):
    if request.method == 'POST':
        correo = request.POST.get('username')
        contraseña = request.POST.get('password')

        try:
            usuario = Usuario.objects.get(correo=correo)

            # Compara la contraseña ingresada con la encriptada en tu modelo Usuario
            if check_password(contraseña, usuario.contraseña):
                # Guarda datos en la sesión
                request.session['usuario_id'] = usuario.rut_usuario
                request.session['nombre'] = usuario.nombre
                
                # Manejo seguro si tipo_de_usuario es nulo
                tipo_str = "desconocido"
                if usuario.tipo_de_usuario:
                    tipo_str = usuario.tipo_de_usuario.tipo_de_usuario
                    request.session['tipo'] = tipo_str

                # Redirección según tipo
                if tipo_str == 'boleteria':
                    return redirect('clases_del_dia')
                elif tipo_str == 'instructor':
                    return redirect('pagina_instructor')
                elif tipo_str == 'director':
                    return redirect('director_dashboard')
                else:
                    messages.error(request, "Tipo de usuario no reconocido.")
            else:
                messages.error(request, "Usuario o contraseña incorrectos.")
        except Usuario.DoesNotExist:
            messages.error(request, "No existe un usuario con ese correo.")

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# --- VISTAS DE REGISTRO (LOGICA ACTUALIZADA) ---

def registrar_usuario(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        
        # Nota: Asegúrate que en forms.py, RegistroForm NO tenga campos de password requeridos
        if form.is_valid():
            correo = form.cleaned_data.get("correo")
            rut_raw = form.cleaned_data.get("rut_usuario") # Obtenemos el RUT

            # 1. GENERAR CONTRASEÑA (RUT sin dígito verificador)
            # Limpiamos puntos y comas
            rut_limpio = rut_raw.replace('.', '').replace(',', '')
            
            # Separamos el DV (todo antes del guion)
            if '-' in rut_limpio:
                password_generada = rut_limpio.split('-')[0]
            else:
                # Si por alguna razón no tiene guion, quitamos el último caracter
                password_generada = rut_limpio[:-1]

            # 2. Crear o actualizar auth.User (Sistema de Django)
            user, created = User.objects.get_or_create(
                username=correo,
                defaults={
                    "email": correo,
                },
            )
            # Asignamos la contraseña generada
            user.set_password(password_generada)
            user.is_active = True
            user.save()

            # 3. Guardar tu modelo Usuario personalizado
            usuario = form.save(commit=False)
            
            # Guardamos la contraseña encriptada también en tu modelo (para tu login_view)
            usuario.contraseña = make_password(password_generada)
            
            # El campo centro_de_esqui ya viene en el form, así que se guardará al hacer save()
            usuario.save()

            messages.success(request, f"Usuario registrado. Tu contraseña es tu RUT sin dígito verificador ({password_generada})")
            return redirect('login')
        else:
            messages.error(request, f"Errores en el formulario: {form.errors}")
    else:
        form = RegistroForm()

    return render(request, 'registrar_usuario.html', {'form': form})


# --- VISTAS DEL DIRECTOR ---

def es_director(user):
    # Ajusta esta validación según cómo manejas los roles en auth.User vs Usuario
    return getattr(user, 'rol', '') == 'director'

@login_required
@user_passes_test(es_director)
def pagina_director(request):
    return render(request, 'director/dashboard.html')


# --- API VIEWS ---

class InstructorPerfilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            perfil = Usuario.objects.get(correo=request.user.username)
        except Usuario.DoesNotExist:
            return Response({"error": "Perfil de instructor no encontrado"}, status=404)

        today = localdate()
        es_activo_hoy = EstadoInstructor.objects.filter(
            instructor=perfil,
            fecha=today,
            activo=True
        ).exists()

        now = datetime.now()
        clases_mes = Clase.objects.filter(
            rut_usuario=perfil,
            hora_inicio__year=now.year,
            hora_inicio__month=now.month
        )

        resultado = clases_mes.aggregate(
            sum_min=Sum('duracion'), 
            sum_alum=Sum('cantidad_alumnos')
        )

        total_horas = int((resultado['sum_min'] or 0) / 60)
        total_alumnos = resultado['sum_alum'] or 0

        serializer = UsuarioSerializer(perfil)
        data = dict(serializer.data)
        
        data['total_horas'] = total_horas
        data['total_alumnos'] = total_alumnos
        data['activo_hoy'] = es_activo_hoy 

        return Response(data)

# Dejé solo UNA definición de InstructorClasesView (la más completa)
class InstructorClasesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        instructor = request.user 
        
        try:
            perfil = Usuario.objects.get(correo=instructor.username)
        except Usuario.DoesNotExist:
            return Response({"error": "Perfil no encontrado"}, status=404)

        fecha_str = request.GET.get("fecha")
        desde_str = request.GET.get("desde")
        hasta_str = request.GET.get("hasta")
        
        # 1. Filtro por Rango
        if desde_str and hasta_str:
            desde = datetime.strptime(desde_str, "%Y-%m-%d").date()
            hasta = datetime.strptime(hasta_str, "%Y-%m-%d").date()
            
            clases = Clase.objects.filter(
                rut_usuario=perfil,
                hora_inicio__date__gte=desde, 
                hora_inicio__date__lte=hasta, 
            ).order_by("hora_inicio")

        # 2. Filtro por Día Específico
        elif fecha_str:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            clases = Clase.objects.filter(
                rut_usuario=perfil,
                hora_inicio__date=fecha,
            ).order_by("hora_inicio")
            
        # 3. Filtro por Todo el Historial
        else:
            clases = Clase.objects.filter(
                rut_usuario=perfil,
            ).order_by("-hora_inicio")

        serializer = ClaseSerializer(clases, many=True)
        return Response({"results": serializer.data})