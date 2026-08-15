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
    ('Ropa', 'Ropa'),
    ('Bolsas', 'Bolsas'),
]

UNIDAD_MEDIDA_CHOICES = [
    ('Unidad', 'Unidad'),
    ('Docena', 'Docena'),
    ('Ciento', 'Ciento'),
    ('Metro', 'Metro'),
    ('Kilo', 'Kilo'),
]

class ProductoForm(forms.ModelForm):

    # ==========================================
    # FOTO DEL PRODUCTO
    # ==========================================

    archivo_imagen = forms.ImageField(
        required=False,
        label='Foto del producto',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'capture': 'environment',
        })
    )

    # ==========================================
    # NOMBRE EDITABLE DE LA IMAGEN
    # ==========================================

    nombre_imagen = forms.CharField(
        required=False,
        max_length=150,
        label='Nombre de la imagen',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ejemplo: arroz-costeno',
        })
    )

    class Meta:
        model = Producto

        fields = [
            'nombre',
            'precio',
            'costo',
            'stock',
            'tipoProducto',
            'unidadMedida',
            'fechaVencimiento',
            'detalle',
            'archivo_imagen',
            'nombre_imagen',
        ]

        widgets = {

            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto',
            }),

            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
            }),

            'costo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
            }),

            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
            }),

            'tipoProducto': forms.Select(
                choices=TIPO_PRODUCTO_CHOICES,
                attrs={
                    'class': 'form-select',
                }
            ),

            'unidadMedida': forms.Select(
                choices=UNIDAD_MEDIDA_CHOICES,
                attrs={
                    'class': 'form-select',
                }
            ),

            'fechaVencimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),

            'detalle': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detalle del producto',
            }),
        }
