from django.urls import path
from . import views

urlpatterns = [
    path('registro/', views.registro_cliente, name='registro_cliente'),
    path('lista/', views.lista_clientes, name='lista_clientes'),
    path('editar/<int:pk>/', views.editar_cliente, name='editar_cliente'),
    path('eliminar/<int:pk>/', views.eliminar_cliente, name='eliminar_cliente'),
]
