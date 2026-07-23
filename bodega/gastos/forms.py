from django import forms
from .models import Proveedor


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'email', 'telefono', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del proveedor'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'value': '@gmail.com', 'placeholder': 'correo@proveedor.com'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'value': '999999999','placeholder': '+51 999 999 999'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Dirección del proveedor', 'rows': 3}),
        }
