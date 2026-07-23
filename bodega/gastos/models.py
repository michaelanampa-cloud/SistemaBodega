from decimal import Decimal

from django.conf import settings
from django.db import models

from productos.models import Producto


class Proveedor(models.Model):
    nombre = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['-fecha_registro']
        verbose_name_plural = 'Proveedores'


class Gasto(models.Model):
    TIPO_COMPRA_CHOICES = [
        ('yape', 'Yape'),
        ('efectivo', 'Efectivo'),
        ('fiado', 'Fiado'),
    ]

    codigo = models.CharField(max_length=50, unique=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    tipo_compra = models.CharField(max_length=20, choices=TIPO_COMPRA_CHOICES, default='efectivo')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    percepcion = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return f"{self.codigo} - {self.proveedor.nombre}"


class GastoItem(models.Model):
    gasto = models.ForeignKey(Gasto, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True)
    cantidad = models.PositiveIntegerField()
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"


class GastoBonificacion(models.Model):
    gasto = models.ForeignKey(Gasto, related_name='bonificaciones', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()

    def __str__(self):
        return f"Bonificación: {self.cantidad} x {self.producto.nombre}"
