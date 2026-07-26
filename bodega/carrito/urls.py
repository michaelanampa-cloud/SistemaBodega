from django.urls import path
from . import views

urlpatterns = [
    path('', views.carrito_view, name='carrito'),
    path('agregar/<int:pk>/', views.agregar_carrito, name='agregar_carrito'),
    path('actualizar/', views.actualizar_carrito, name='actualizar_carrito'),
    path('eliminar/<int:pk>/', views.eliminar_carrito, name='eliminar_carrito'),
    path('comprar/', views.registrar_compra, name='registrar_compra'),
    path('lista-compras/', views.lista_compras, name='lista_compras'),
    path('detalle/<int:pk>/', views.compra_detalle, name='compra_detalle'),
    path('detalle/<int:pk>/pdf/', views.exportar_pdf, name='exportar_pdf'),
    path('buscar-producto/', views.buscar_producto, name='buscar_producto'),
]
