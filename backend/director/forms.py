from django import forms
from usuarios.models import Usuario, Identificador
from django.contrib.auth.hashers import make_password

class InstructorForm(forms.ModelForm):
    contraseña = forms.CharField(widget=forms.PasswordInput, required=True, label="Contraseña")

    class Meta:
        model = Usuario
        fields = [
            'rut_usuario', 'nombre', 'apellido',
            'correo', 'numero_telefono',
            'disciplina', 'nivel_instructor', 'idioma'
        ]

    def save(self, commit=True, center=None):
        inst = super().save(commit=False)
        inst.tipo_de_usuario = Identificador.objects.get(pk='instructor')
        inst.id_centro = center                          # <-- centro del director
        inst.contraseña = make_password(self.cleaned_data['contraseña'])
        if commit:
            inst.save()
        return inst
