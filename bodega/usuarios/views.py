from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404

# Envío de correo
from django.core.mail import send_mail
from django.conf import settings

from .forms import RegistroForm, LoginForm, EditarPerfilForm, CambiarPasswordForm, CrearUsuarioForm, EditarUsuarioAdminForm

@login_required
def registro_view(request):
    if not es_administrador(request.user):
        messages.error(
            request,
            'No tienes permisos para registrar nuevos usuarios.'
        )
        return redirect('perfil')
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'El usuario "{user.username}" fue creado correctamente.'
            )
            return redirect('registro')
    else:
        form = RegistroForm()
    return render(
        request,
        'usuarios/registro.html',
        {'form': form}
    )


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

@login_required
def editar_perfil_view(request):
	if request.method == 'POST':
		form = EditarPerfilForm(
			request.POST,
			instance=request.user
		)
		if form.is_valid():
			form.save()
			messages.success(
				request,
				'Tu perfil ha sido actualizado correctamente.'
			)
			return redirect('perfil')
	else:
		form = EditarPerfilForm(
			instance=request.user
		)
	return render(
		request,
		'usuarios/editar_perfil.html',
		{'form': form}
	)




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

@login_required
def cambiar_password_view(request):
    if request.method == 'POST':
        form = CambiarPasswordForm(
            request.user,
            request.POST
        )
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Tu contraseña ha sido cambiada correctamente. '
                'Por seguridad, inicia sesión nuevamente.'
            )
            logout(request)
            return redirect('login')
    else:
        form = CambiarPasswordForm(
            request.user
        )
    return render(
        request,
        'usuarios/cambiar_password.html',
        {'form': form}
    )

def es_administrador(user):
    return (
        user.is_authenticated
        and (
            user.is_superuser
            or user.groups.filter(name='Administrador').exists()
        )
    )

@login_required
def lista_usuarios_view(request):
	if not request.user.has_perm('auth.view_user'):

		messages.error(
			request,
			'No tienes permisos para ver los usuarios.'
		)
		return redirect('perfil')

	usuarios = User.objects.all().order_by(
		'username'
	)

	return render(
		request,
		'usuarios/lista_usuarios.html',
		{
			'usuarios': usuarios
		}
	)

@login_required
def crear_usuario_view(request):
	if not request.user.has_perm('auth.add_user'):

		messages.error(
			request,
			'No tienes permisos para crear usuarios.'
		)

		return redirect('perfil')


	if request.method == 'POST':

		form = CrearUsuarioForm(
			request.POST
		)

		if form.is_valid():

			user = form.save()

			messages.success(
				request,
				f'El usuario "{user.username}" '
				f'fue creado correctamente.'
			)

			return redirect('lista_usuarios')

	else:

		form = CrearUsuarioForm()


	return render(
		request,
		'usuarios/crear_usuario.html',
		{
			'form': form
		}
	)

@login_required
def editar_usuario_view(request, pk):
	if not request.user.has_perm('auth.change_user'):

		messages.error(
			request,
			'No tienes permisos para editar usuarios.'
		)

		return redirect('perfil')


	usuario = get_object_or_404(
		User,
		pk=pk
	)


	# Evitar que un administrador
	# se desactive a sí mismo.
	if (
		usuario.pk == request.user.pk
		and request.method == 'POST'
		and not request.POST.get('is_active')
	):

		messages.error(
			request,
			'No puedes desactivar tu propia cuenta.'
		)

		return redirect(
			'editar_usuario',
			pk=pk
		)


	if request.method == 'POST':

		form = EditarUsuarioAdminForm(
			request.POST,
			instance=usuario
		)

		if form.is_valid():

			usuario = form.save(
				commit=False
			)

			usuario.save()

			rol = form.cleaned_data['rol']

			usuario.groups.set([rol])


			messages.success(
				request,
				f'El usuario "{usuario.username}" '
				f'fue actualizado correctamente.'
			)

			return redirect(
				'lista_usuarios'
			)

	else:

		form = EditarUsuarioAdminForm(
			instance=usuario
		)


	return render(
		request,
		'usuarios/editar_usuario.html',
		{
			'form': form,
			'usuario': usuario
		}
	)
