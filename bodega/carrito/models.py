from decimal import Decimal

from django.conf import settings
from django.db import models

from productos.models import Producto
from clientes.models import Cliente


class Compra(models.Model):
    TIPO_COMPRA_CHOICES = [
        ('yape', 'Yape'),
        ('efectivo', 'Efectivo'),
        ('fiado', 'Fiado'),
    ]
    
    codigo = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    adicional = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tipo_compra = models.CharField(max_length=20, choices=TIPO_COMPRA_CHOICES, default='efectivo')
    estado = models.CharField(max_length=50, default='Registrada')

    def __str__(self):
        return f"{self.codigo} - {self.fecha:%d/%m/%Y}"


class CompraItem(models.Model):
    compra = models.ForeignKey(Compra, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"
