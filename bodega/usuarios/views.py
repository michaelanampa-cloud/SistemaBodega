from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse

# Envío de correo
from django.core.mail import send_mail
from django.conf import settings

from .forms import RegistroForm, LoginForm


def registro_view(request):
	if request.user.is_authenticated:
		return redirect('perfil')

	if request.method == 'POST':
		form = RegistroForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			messages.success(request, 'Registro exitoso. Bienvenido.')
			return redirect('perfil')
	else:
		form = RegistroForm()
	return render(request, 'usuarios/registro.html', {'form': form})


def login_view(request):
	if request.user.is_authenticated:
		return redirect('perfil')

	if request.method == 'POST':
		form = LoginForm(request, data=request.POST)
		if form.is_valid():
			user = form.get_user()
			login(request, user)
			messages.success(request, 'Has iniciado sesión.')
			next_url = request.GET.get('next') or reverse('perfil')
			return redirect(next_url)
	else:
		form = LoginForm()
	return render(request, 'usuarios/login.html', {'form': form})


def logout_view(request):
	logout(request)
	messages.info(request, 'Has cerrado sesión.')
	return redirect('login')


@login_required
def perfil_view(request):
	return render(request, 'usuarios/perfil.html', {'user': request.user})


def inicio_view(request):
	"""Página de inicio con mensaje de bienvenida. Si el usuario está autenticado,
	se muestra saludo personalizado; el menú en `base.html` controla la visibilidad.
	"""
	if request.user.is_authenticated:
		mensaje = f"Bienvenido, {request.user.username}!"
	else:
		mensaje = "Bienvenido a Bodega. Por favor, inicia sesión para ver todas las opciones."
	return render(request, 'usuarios/inicio.html', {'mensaje': mensaje})


def contacto_view(request):
	"""Renderiza la página de contacto y procesa envíos simples del formulario."""
	if request.method == 'POST':
		asunto = request.POST.get('asunto')
		numero = request.POST.get('numero')
		correo = request.POST.get('correo')
		mensaje = request.POST.get('mensaje')
		# Construir cuerpo del correo
		asunto_email = f"Contacto web: {asunto}"
		cuerpo = f"Has recibido un nuevo mensaje desde la página de contacto.\n\n"
		cuerpo += f"De: {correo}\n"
		cuerpo += f"Teléfono: {numero}\n\n"
		cuerpo += f"Mensaje:\n{mensaje}\n"

		to_email = ['michaelanampa@gmail.com']
		from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'webmaster@localhost')

		try:
			send_mail(asunto_email, cuerpo, from_email, to_email, fail_silently=False)
			messages.success(request, 'Gracias. Tu mensaje ha sido enviado correctamente.')
		except Exception as e:
			messages.error(request, 'Error al enviar el mensaje. Intenta más tarde.')
		return redirect('contacto')

	return render(request, 'usuarios/contacto.html')
