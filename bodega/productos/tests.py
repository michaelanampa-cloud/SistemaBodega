from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Producto

User = get_user_model()


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

    def test_imprimir_etiquetas_seleccionadas_generates_pdf(self):
        producto_1 = Producto.objects.create(
            nombre='Pan Integral',
            precio=8.20,
            costo=5.50,
            stock=10,
            tipoProducto='Panadería',
            unidadMedida='Unidad',
            detalle='Pan integral',
        )
        producto_2 = Producto.objects.create(
            nombre='Leche Entera',
            precio=6.80,
            costo=4.20,
            stock=14,
            tipoProducto='Lácteos',
            unidadMedida='Unidad',
            detalle='Leche entera',
        )

        response = self.client.post(
            reverse('imprimir_etiquetas_productos'),
            {'producto_ids': [str(producto_1.pk), str(producto_2.pk)]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_guardar_seleccion_productos_persiste_en_sesion(self):
        producto = Producto.objects.create(
            nombre='Yogur Natural',
            precio=7.00,
            costo=4.00,
            stock=9,
            tipoProducto='Lácteos',
            unidadMedida='Unidad',
            detalle='Yogur natural',
        )

        response = self.client.post(
            reverse('guardar_seleccion_productos'),
            {'producto_id': str(producto.pk), 'accion': 'agregar'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(producto.pk, self.client.session.get('productos_seleccionados', []))

    def test_producto_puede_agregarse_y_quitarse_de_ofertas(self):
        producto = Producto.objects.create(
            nombre='Queso Fresco',
            precio=18.00,
            costo=11.00,
            stock=6,
            tipoProducto='Lácteos',
            unidadMedida='Unidad',
            detalle='Queso fresco',
        )

        response = self.client.post(reverse('toggle_oferta_producto', args=[producto.pk]))
        self.assertEqual(response.status_code, 302)
        producto.refresh_from_db()
        self.assertTrue(producto.en_oferta)
        self.assertEqual(producto.descuento_oferta, 10.00)

        response = self.client.post(reverse('toggle_oferta_producto', args=[producto.pk]))
        self.assertEqual(response.status_code, 302)
        producto.refresh_from_db()
        self.assertFalse(producto.en_oferta)

    def test_ofertas_productos_muestra_productos_en_oferta(self):
        producto = Producto.objects.create(
            nombre='Jugo de Naranja',
            precio=12.50,
            costo=8.00,
            stock=11,
            tipoProducto='Bebidas',
            unidadMedida='Unidad',
            detalle='Jugo natural',
            en_oferta=True,
            descuento_oferta=10.00,
        )

        response = self.client.get(reverse('ofertas_productos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, producto.nombre)
        self.assertContains(response, '1,25')

    def test_carrito_aplica_descuento_en_productos_en_oferta(self):
        user = User.objects.create_user(username='carrito_user', password='12345')
        producto = Producto.objects.create(
            nombre='Aceite Premium',
            precio=20.00,
            costo=12.00,
            stock=10,
            tipoProducto='Abarrotes',
            unidadMedida='Unidad',
            detalle='Aceite de oliva',
            en_oferta=True,
            descuento_oferta=10.00,
        )

        self.client.force_login(user)
        session = self.client.session
        session['carrito'] = {str(producto.pk): '2'}
        session.save()

        response = self.client.get(reverse('carrito'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'S/ 18,00')
        self.assertContains(response, 'S/ 36,00')
