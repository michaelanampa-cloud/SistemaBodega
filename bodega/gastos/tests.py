from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from productos.models import Producto
from .models import Proveedor


class ProveedorViewsTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='secret123')
        self.client.force_login(self.user)
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Uno',
            email='proveedor@example.com',
            telefono='999999999',
            direccion='Av. Ejemplo 123',
        )

    def test_editar_proveedor_actualiza_datos(self):
        response = self.client.post(
            reverse('editar_proveedor', args=[self.proveedor.pk]),
            {
                'nombre': 'Proveedor Editado',
                'email': 'editado@example.com',
                'telefono': '111111111',
                'direccion': 'Nueva dirección',
            },
        )

        self.assertRedirects(response, reverse('lista_proveedores'))
        self.proveedor.refresh_from_db()
        self.assertEqual(self.proveedor.nombre, 'Proveedor Editado')
        self.assertEqual(self.proveedor.email, 'editado@example.com')

    def test_eliminar_proveedor_desactiva_registro(self):
        response = self.client.post(reverse('eliminar_proveedor', args=[self.proveedor.pk]))

        self.assertRedirects(response, reverse('lista_proveedores'))
        self.proveedor.refresh_from_db()
        self.assertFalse(self.proveedor.activo)

    def test_buscar_productos_incluye_codigo_barras_y_descripcion(self):
        producto = Producto.objects.create(
            nombre='Leche Entera',
            precio=7.50,
            costo=5.00,
            stock=20,
            tipoProducto='Lácteos',
            unidadMedida='Unidad',
            detalle='Leche entera de la granja',
            codigo_barras='1234567890123',
        )

        response = self.client.get(reverse('buscar_productos'), {'q': '1234567890123'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['id'], producto.pk)

        response = self.client.get(reverse('buscar_productos'), {'q': 'granja'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['id'], producto.pk)
