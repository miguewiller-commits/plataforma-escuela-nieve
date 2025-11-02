from django import forms
from usuarios.models import Usuario, Identificador

class LoginForm(forms.Form):
    username = forms.CharField(label='Usuario')
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)

class RegistroForm(forms.ModelForm):
    contraseña = forms.CharField(widget=forms.PasswordInput)
    confirmar_contraseña = forms.CharField(widget=forms.PasswordInput)

    # si es FK:
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
            "tipo_de_usuario",
            "disciplina",
            "nivel_instructor",
            "idioma",
            "contraseña",
        ]

    def clean(self):
        cd = super().clean()

        # contraseñas iguales
        if cd.get("contraseña") != cd.get("confirmar_contraseña"):
            self.add_error("confirmar_contraseña", "Las contraseñas no coinciden")

        tipo = cd.get("tipo_de_usuario")
        # si usas FK, tipo.tipo_de_usuario es la cadena ('instructor', 'boleteria', etc.)
        tipo_str = ""
        if tipo is not None:
            tipo_str = getattr(tipo, "tipo_de_usuario", str(tipo)).lower()

        es_instructor = (tipo_str == "instructor")

        # requeridos solo para instructores
        if es_instructor:
            if not cd.get("disciplina"):
                self.add_error("disciplina", "Obligatorio para instructores.")
            if not cd.get("nivel_instructor"):
                self.add_error("nivel_instructor", "Obligatorio para instructores.")
            if not cd.get("idioma"):
                self.add_error("idioma", "Obligatorio para instructores.")
        else:
            # normaliza/limpia si no es instructor
            cd["disciplina"] = None
            cd["nivel_instructor"] = None
            cd["idioma"] = ""

        return cd