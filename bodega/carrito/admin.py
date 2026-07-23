from django.contrib import admin

from .models import Compra, CompraItem


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'user', 'fecha', 'total', 'estado')
    search_fields = ('codigo', 'user__username')
    list_filter = ('estado',)


@admin.register(CompraItem)
class CompraItemAdmin(admin.ModelAdmin):
    list_display = ('compra', 'producto', 'cantidad', 'precio', 'subtotal')
    search_fields = ('producto__nombre',)
