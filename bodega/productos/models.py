from django.db import models


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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} ({self.tipoProducto})"
