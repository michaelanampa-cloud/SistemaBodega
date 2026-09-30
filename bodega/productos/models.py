import hashlib
import os

from barcode import Code128, get_barcode_class
from barcode.writer import ImageWriter
from django.conf import settings
from django.db import models
from django.utils import timezone


class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stock = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tipoProducto = models.CharField(max_length=100)
    unidadMedida = models.CharField(max_length=50, blank=True)
    fechaVencimiento = models.DateField(blank=True, null=True)
    detalle = models.TextField(blank=True)
    imagen = models.CharField(max_length=255, blank=True)
    codigo_barras = models.CharField(max_length=13, unique=True, blank=True, null=True)
    codigo_barras_imagen = models.CharField(max_length=255, blank=True, default='')
    en_oferta = models.BooleanField(default=False)
    descuento_oferta = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def _calcular_digito_verificador(base12):
        total = 0
        for index, digit in enumerate(base12):
            weight = 1 if index % 2 == 0 else 3
            total += int(digit) * weight
        return str((10 - (total % 10)) % 10)

    def _generar_codigo_barras(self):
        if self.codigo_barras and self.codigo_barras.isdigit() and len(self.codigo_barras) == 13:
            return self.codigo_barras

        seed_text = f"{self.pk or 'nuevo'}|{self.nombre}|{self.created_at or timezone.now()}|{timezone.now().timestamp()}"
        digest = hashlib.md5(seed_text.encode('utf-8')).hexdigest()
        base12 = str(int(digest[:12], 16) % 10**12).zfill(12)
        return f"{base12}{self._calcular_digito_verificador(base12)}"

    def _crear_imagen_codigo_barras(self):
        if not self.codigo_barras:
            return

        carpeta = os.path.join(settings.BASE_DIR, 'static', 'img', 'codigos_barra')
        os.makedirs(carpeta, exist_ok=True)

        nombre_archivo = f"codigo_{self.pk or self.codigo_barras}.png"
        ruta_base = os.path.join(carpeta, nombre_archivo.replace('.png', ''))

        try:
            codigo = Code128(self.codigo_barras, writer=ImageWriter())
            codigo.save(
                ruta_base,
                options={
                    'write_text': True,
                    'text_distance': 4,
                    'module_height': 13,
                    'module_width': 1.8,
                    'quiet_zone': 6,
                    'font_size': 12,
                }
            )
            self.codigo_barras_imagen = f"img/codigos_barra/{nombre_archivo}"
        except Exception:
            self.codigo_barras_imagen = ''

    def save(self, *args, **kwargs):
        if self.codigo_barras:
            try:
                int(self.codigo_barras)
            except (TypeError, ValueError):
                self.codigo_barras = self._generar_codigo_barras()
            if len(self.codigo_barras) != 13:
                self.codigo_barras = self._generar_codigo_barras()
        else:
            self.codigo_barras = self._generar_codigo_barras()

        super().save(*args, **kwargs)

        if not self.codigo_barras_imagen:
            self._crear_imagen_codigo_barras()
            super().save(update_fields=['codigo_barras_imagen'])

    @property
    def descuento_valor(self):
        if not self.en_oferta:
            return 0
        return self.precio * (self.descuento_oferta / 100)

    @property
    def precio_descuento(self):
        if not self.en_oferta:
            return self.precio
        return self.precio - self.descuento_valor

    def __str__(self):
        return f"{self.nombre} ({self.tipoProducto})"
