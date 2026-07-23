from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('resumen-gastos/', views.resumen_gastos, name='resumen_gastos'),
    path('resumen-compras/', views.resumen_compras, name='resumen_compras'),
]
