from django.core.management.base import BaseCommand

from productos.models import Producto


class Command(BaseCommand):
    help = 'Genera un código de barras para cada producto registrado.'

    def handle(self, *args, **options):
        productos = Producto.objects.all().order_by('id')
        total = 0

        for producto in productos:
            if not producto.codigo_barras or len(producto.codigo_barras) != 13:
                producto.codigo_barras = ''
            producto.save()
            total += 1

        self.stdout.write(self.style.SUCCESS(f'Se generaron códigos de barras para {total} productos.'))
