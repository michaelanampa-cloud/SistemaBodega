from django.contrib import admin
from .models import Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
	list_display = ('nombre', 'tipoProducto', 'precio', 'stock')
	search_fields = ('nombre', 'tipoProducto')
	list_filter = ('tipoProducto',)
