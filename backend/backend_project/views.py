# app/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm,RegistroForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from usuarios.models import Usuario, Identificador
from django.contrib.auth.hashers import make_password, check_password # para encriptar contraseña
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from clases.models import Clase
from datetime import datetime

def login_view(request):
    if request.method == 'POST':
        correo = request.POST.get('username')
        contraseña = request.POST.get('password')

        try:
            usuario = Usuario.objects.get(correo=correo)

            # Compara la contraseña ingresada con la encriptada
            if check_password(contraseña, usuario.contraseña):
                # Guarda datos en la sesión
                request.session['usuario_id'] = usuario.rut_usuario
                request.session['nombre'] = usuario.nombre
                request.session['tipo'] = usuario.tipo_de_usuario.tipo_de_usuario

                # Redirección según tipo de usuario
                tipo = usuario.tipo_de_usuario.tipo_de_usuario
                if tipo == 'boleteria':
                    return redirect('clases_del_dia')  # URL name de tu vista
                elif tipo == 'instructor':
                    return redirect('pagina_instructor')
                elif tipo == 'director':
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

def es_director(user):
    return user.rol == 'director'

@login_required
@user_passes_test(es_director)
def pagina_director(request):
    return render(request, 'director/dashboard.html')


def registrar_usuario(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)

            # Encriptar contraseña
            usuario.contraseña = make_password(form.cleaned_data["contraseña"])

            usuario.save()
            messages.success(request, "Usuario registrado correctamente.")
            return redirect('login')
    else:
        form = RegistroForm()

    return render(request, 'registrar_usuario.html', {'form': form})

class InstructorClasesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # instructor = request.user (asumiendo que user es el instructor)
        instructor = request.user

        fecha_str = request.GET.get("fecha")
        if fecha_str:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            clases = Clase.objects.filter(
                rut_usuario=instructor,
                hora_inicio__date=fecha,
            ).order_by("hora_inicio")
        else:
            clases = Clase.objects.filter(
                rut_usuario=instructor,
            ).order_by("-hora_inicio")[:50]

        data = []
        for c in clases:
            data.append({
                "id": c.id_clase,
                "hora_inicio": c.hora_inicio.isoformat(),
                "hora_fin": c.hora_fin.isoformat(),
                "disciplina": c.disciplina_clase,
                "nivel": c.nivel_clase,
                "nombre_titular": c.nombre_titular,
                "telefono": c.titular_telefono,
                "cantidad_alumnos": c.cantidad_alumnos,
            })

        return Response({"results": data})