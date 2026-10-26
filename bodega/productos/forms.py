from calendar import monthrange
from datetime import date

from django import forms
from django.core.validators import RegexValidator

from .models import Producto


def fecha_default_vencimiento():
    hoy = date.today()
    mes_nuevo = hoy.month + 6
    anio_nuevo = hoy.year + (mes_nuevo - 1) // 12
    mes_nuevo = ((mes_nuevo - 1) % 12) + 1
    ultimo_dia = monthrange(anio_nuevo, mes_nuevo)[1]
    dia = min(hoy.day, ultimo_dia)
    return date(anio_nuevo, mes_nuevo, dia)


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

ZONA_CHOICES = [
    ('zona1', 'zona1'),
    ('zona2', 'zona2'),
    ('zona3', 'zona3'),
    ('zona4', 'zona4'),
    ('zona5', 'zona5'),
    ('zona6', 'zona6'),
    ('zona7', 'zona7'),
    ('zona8', 'zona8'),
    ('EqFrio1', 'EqFrio1'),
    ('EqFrio2', 'EqFrio2'),
    ('EqFrio3', 'EqFrio3'),
    ('EqFrio4', 'EqFrio4'),
    ('EqFrio5', 'EqFrio5'),
]

UNIDAD_MEDIDA_CHOICES = [
    ('Unidad', 'Unidad'),
    ('Docena', 'Docena'),
    ('Ciento', 'Ciento'),
    ('Metro', 'Metro'),
    ('Kilo', 'Kilo'),
]


def zona_por_tipo(tipo):
    mapping = {
        'Cerveza': 'zona1',
        'Abarrotes': 'zona2',
        'Limpieza': 'zona2',
        'Gaseosa': 'zona3',
        'Aguas': 'zona3',
        'Utiles': 'zona4',
        'Ropa': 'zona5',
        'Bolsas': 'zona5',
        'Galleta': 'zona6',
        'Verduras_Frutas': 'zona7',
        'Snack': 'zona8',
        'Helado': 'EqFrio1',
        'Bebidas': 'EqFrio2',
    }
    return mapping.get(tipo, 'zona1')


class ProductoForm(forms.ModelForm):
    archivo_imagen = forms.ImageField(
        required=False,
        label='Foto del producto',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'capture': 'environment',
        })
    )

    nombre_imagen = forms.CharField(
        required=False,
        max_length=150,
        label='Nombre de la imagen',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ejemplo: arroz-costeno',
        })
    )

    codigo_barras = forms.CharField(
        required=False,
        max_length=13,
        min_length=13,
        label='Código de barras',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Se genera automáticamente',
            'maxlength': '13',
            'inputmode': 'numeric',
        }),
        validators=[
            RegexValidator(
                regex=r'^\d{13}$',
                message='El código de barras debe tener exactamente 13 dígitos.',
            )
        ],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and not self.initial.get('fechaVencimiento'):
            self.initial['fechaVencimiento'] = fecha_default_vencimiento()
        elif self.instance and not self.instance.fechaVencimiento and not self.initial.get('fechaVencimiento'):
            self.initial['fechaVencimiento'] = fecha_default_vencimiento()

        tipo_actual = self.data.get('tipoProducto') if self.data else getattr(self.instance, 'tipoProducto', '')
        if tipo_actual:
            self.initial['zona'] = zona_por_tipo(tipo_actual)
        elif not self.initial.get('zona') and getattr(self.instance, 'tipoProducto', ''):
            self.initial['zona'] = zona_por_tipo(self.instance.tipoProducto)

    class Meta:
        model = Producto
        fields = [
            'nombre',
            'precio',
            'costo',
            'stock',
            'tipoProducto',
            'unidadMedida',
            'zona',
            'fechaVencimiento',
            'detalle',
            'codigo_barras',
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
                attrs={'class': 'form-select'}
            ),
            'unidadMedida': forms.Select(
                choices=UNIDAD_MEDIDA_CHOICES,
                attrs={'class': 'form-select'}
            ),
            'zona': forms.Select(
                choices=ZONA_CHOICES,
                attrs={'class': 'form-select'}
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
            'codigo_barras': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Se genera automáticamente',
                'maxlength': '13',
                'inputmode': 'numeric',
            }),
        }
