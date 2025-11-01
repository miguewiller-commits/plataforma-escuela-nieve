from django import forms
from usuarios.models import Usuario, Identificador

class LoginForm(forms.Form):
    username = forms.CharField(label='Usuario')
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)

class RegistroForm(forms.ModelForm):
    contraseña = forms.CharField(widget=forms.PasswordInput)
    confirmar_contraseña = forms.CharField(widget=forms.PasswordInput)

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
        cleaned_data = super().clean()
        contraseña = cleaned_data.get("contraseña")
        confirmar = cleaned_data.get("confirmar_contraseña")

        if contraseña != confirmar:
            raise forms.ValidationError("Las contraseñas no coinciden")

        return cleaned_data

