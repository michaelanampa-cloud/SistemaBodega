from django import forms
from .models import Producto

TIPO_PRODUCTO_CHOICES = [
    ('Cerveza', 'Cerveza'),
    ('Abarrotes', 'Abarrotes'),
    ('Gaseosa', 'Gaseosa'),
    ('Snack', 'Snack'),
    ('Galleta', 'Galleta'),
    ('Bebidas', 'Bebidas'),
    ('Limpieza', 'Limpieza'),
    ('Helado', 'Helado'),
    ('Utiles', 'Utiles'),
    ('Aguas', 'Aguas'),
    ('Verduras_Frutas', 'Verduras/Frutas'),
]

UNIDAD_MEDIDA_CHOICES = [
    ('Unidad', 'Unidad'),
    ('Docena', 'Docena'),
    ('Ciento', 'Ciento'),
    ('Metro', 'Metro'),
    ('Kilo', 'Kilo'),
]


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'precio', 'costo', 'stock', 'tipoProducto', 'unidadMedida', 'fechaVencimiento', 'detalle', 'imagen']
        widgets = {
            'fechaVencimiento': forms.DateInput(attrs={'type': 'date'}),
            'detalle': forms.Textarea(attrs={'rows': 2}),
            'tipoProducto': forms.Select(choices=TIPO_PRODUCTO_CHOICES),
            'unidadMedida': forms.Select(choices=UNIDAD_MEDIDA_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
