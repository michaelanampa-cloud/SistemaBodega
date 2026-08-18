from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['dni','nombre', 'email', 'telefono', 'direccion']
        widgets = {
            'dni': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese DNI de 8 dígitos',
                'maxlength': '8',
                'inputmode': 'numeric',
                'autocomplete': 'off',
                'id': 'id_dni'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del cliente'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'value': '@gmail.com',
                'placeholder': 'correo@ejemplo.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+51 999 999 999'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección del cliente',
                'rows': 3
            }),
        }
