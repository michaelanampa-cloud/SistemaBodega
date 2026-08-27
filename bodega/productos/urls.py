from django.urls import path
from . import views

urlpatterns = [
	path('registros/', views.registros_productos, name='registros_productos'),
	path('vencer/', views.productos_vencer, name='productos_vencer'),
	path('', views.lista_productos, name='lista_productos'),
	path('<int:pk>/', views.detalle_producto, name='detalle_producto'),
	path('<int:pk>/editar/', views.editar_producto, name='editar_producto'),
	path('<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    path('stock/', views.productos_stock, name='productos_stock'),
]
