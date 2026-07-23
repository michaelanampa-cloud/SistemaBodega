from django.urls import path
from . import views

urlpatterns = [
	path('', views.inicio_view, name='inicio'),
	path('registro/', views.registro_view, name='registro'),
	path('login/', views.login_view, name='login'),
	path('logout/', views.logout_view, name='logout'),
	path('perfil/', views.perfil_view, name='perfil'),
	path('contacto/', views.contacto_view, name='contacto'),
]
