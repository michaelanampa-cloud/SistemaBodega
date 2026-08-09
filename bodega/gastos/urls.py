from django.urls import path
from . import views

urlpatterns = [
    path('nuevo-proveedor/', views.nuevo_proveedor, name='nuevo_proveedor'),
    path('editar-proveedor/<int:pk>/', views.editar_proveedor, name='editar_proveedor'),
    path('eliminar-proveedor/<int:pk>/', views.eliminar_proveedor, name='eliminar_proveedor'),
    path('lista-proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('registrar-gastos/', views.registrar_gastos, name='registrar_gastos'),
    path('cotizacion/', views.cotizacion, name='cotizacion'),
    path('buscar-productos/', views.buscar_productos, name='buscar_productos'),
    path('lista-gastos/', views.lista_gastos, name='lista_gastos'),
    path('detalle/<int:pk>/', views.detalle_gasto, name='detalle_gasto'),
]
