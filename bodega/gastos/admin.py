from django.contrib import admin

from .models import Proveedor, Gasto, GastoItem


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'telefono', 'activo', 'fecha_registro')
    list_filter = ('activo',)
    search_fields = ('nombre', 'email', 'telefono')


class GastoItemInline(admin.TabularInline):
    model = GastoItem
    extra = 0


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'proveedor', 'tipo_compra', 'total', 'fecha')
    list_filter = ('tipo_compra', 'fecha')
    search_fields = ('codigo', 'proveedor__nombre')
    inlines = [GastoItemInline]

