from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from carrito.models import Compra
from gastos.models import Gasto, Proveedor


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='secret')
        self.proveedor = Proveedor.objects.create(nombre='Proveedor Test')

    def test_dashboard_shows_balance_summary_for_selected_range(self):
        Compra.objects.create(codigo='CMP-001', user=self.user, total=Decimal('120.00'))
        Compra.objects.create(codigo='CMP-002', user=self.user, total=Decimal('80.00'))
        Gasto.objects.create(codigo='GAS-001', proveedor=self.proveedor, user=self.user, total=Decimal('30.00'))

        self.client.login(username='tester', password='secret')
        response = self.client.get(reverse('dashboard'), {
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resumen de balance')
        self.assertContains(response, 'S/ 200,00')
        self.assertContains(response, 'S/ 30,00')
        self.assertContains(response, 'S/ 170,00')
