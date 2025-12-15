from django import forms
from usuarios.models import Usuario, Identificador

class LoginForm(forms.Form):
    username = forms.CharField(label='Usuario')
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)

# --- FORMULARIO DE REGISTRO (Con el arreglo de id_centro) ---
class RegistroForm(forms.ModelForm):
    tipo_de_usuario = forms.ModelChoiceField(
        queryset=Identificador.objects.all(),
        empty_label="Seleccione un tipo de usuario",
        label="Tipo de usuario"
    )

    class Meta:
        model = Usuario
        fields = [
            "rut_usuario",
            "nombre",
            "apellido",
            "correo",
            "numero_telefono",
            "id_centro",       # <--- El campo corregido
            "tipo_de_usuario",
            "disciplina",
            "nivel_instructor",
            "idioma",
        ]

    def clean(self):
        cd = super().clean()

        # Validación lógica para instructores
        tipo = cd.get("tipo_de_usuario")
        tipo_str = ""
        if tipo is not None:
            tipo_str = getattr(tipo, "tipo_de_usuario", str(tipo)).lower()

        es_instructor = ("instructor" in tipo_str)

        if es_instructor:
            if not cd.get("disciplina"):
                self.add_error("disciplina", "Obligatorio para instructores.")
            if not cd.get("nivel_instructor"):
                self.add_error("nivel_instructor", "Obligatorio para instructores.")
            if not cd.get("idioma"):
                self.add_error("idioma", "Obligatorio para instructores.")
        else:
            # Limpiar campos si no es instructor
            cd["disciplina"] = None
            cd["nivel_instructor"] = None
            cd["idioma"] = ""

        return cd