from django.urls import path
from . import views

urlpatterns = [
	path('registros/', views.registros_productos, name='registros_productos'),
	path('vencer/', views.productos_vencer, name='productos_vencer'),
	path('stock/', views.productos_stock, name='productos_stock'),
	path('ofertas/', views.ofertas_productos, name='ofertas_productos'),
	path('seleccionados/', views.productos_seleccionados, name='productos_seleccionados'),
	path('guardar-seleccion/', views.guardar_seleccion_productos, name='guardar_seleccion_productos'),
	path('etiquetas-pdf/', views.imprimir_etiquetas_productos, name='imprimir_etiquetas_productos'),
	path('<int:pk>/toggle-oferta/', views.toggle_oferta_producto, name='toggle_oferta_producto'),
	path('<int:pk>/etiqueta-pdf/', views.imprimir_etiqueta_producto, name='imprimir_etiqueta_producto'),
	path('<int:pk>/editar/', views.editar_producto, name='editar_producto'),
	path('<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
	path('<int:pk>/', views.detalle_producto, name='detalle_producto'),
	path('', views.lista_productos, name='lista_productos'),
]
