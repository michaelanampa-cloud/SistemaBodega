from django.urls import path
from . import views

urlpatterns = [
	path('', views.inicio_view, name='inicio'),
	path('registro/', views.registro_view, name='registro'),
	path('login/', views.login_view, name='login'),
	path('logout/', views.logout_view, name='logout'),
	path('perfil/', views.perfil_view, name='perfil'),
	path('contacto/', views.contacto_view, name='contacto'),
    path('perfil/editar/', views.editar_perfil_view, name='editar_perfil'),
    path('perfil/cambiar-password/', views.cambiar_password_view, name='cambiar_password'),
    # ============================== # GESTIÓN DE USUARIOS # ============================== 
	path('usuarios/', views.lista_usuarios_view, name='lista_usuarios'), 
    path('usuarios/nuevo/', views.crear_usuario_view, name='crear_usuario'), 
    path('usuarios/<int:pk>/editar/', views.editar_usuario_view, name='editar_usuario'), 
    path('contacto/', views.contacto_view, name='contacto'),
]
