from django.test import TestCase

from .models import Producto


class ProductoBarcodeTests(TestCase):
    def test_producto_generates_codigo_barras_automaticamente(self):
        producto = Producto.objects.create(
            nombre='Arroz Premium',
            precio=12.50,
            costo=8.00,
            stock=20,
            tipoProducto='Abarrotes',
            unidadMedida='Kilo',
            detalle='Arroz de calidad',
        )

        self.assertTrue(producto.codigo_barras)
        self.assertEqual(len(producto.codigo_barras), 13)
        self.assertTrue(producto.codigo_barras.isdigit())
