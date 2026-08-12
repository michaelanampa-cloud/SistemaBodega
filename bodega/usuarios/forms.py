from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User, Group


class RegistroForm(UserCreationForm):
	email = forms.EmailField(required=True)

	class Meta:
		model = User
		fields = ("username", "email", "password1", "password2")

	def save(self, commit=True):
		user = super().save(commit=False)
		user.email = self.cleaned_data["email"]
		if commit:
			user.save()
		return user

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# Añadir clase bootstrap a todos los campos
		for field in self.fields.values():
			field.widget.attrs.update({
				'class': 'form-control'
			})


class LoginForm(AuthenticationForm):
	username = forms.CharField(label="Usuario")
	password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['username'].widget.attrs.update({'class': 'form-control'})
		self.fields['password'].widget.attrs.update({'class': 'form-control'})

class EditarPerfilForm(forms.ModelForm):

	class Meta:
		model = User
		fields = (
			'username',
			'email',
			'first_name',
			'last_name',
		)

		labels = {
			'username': 'Nombre de usuario',
			'email': 'Correo electrónico',
			'first_name': 'Nombre',
			'last_name': 'Apellidos',
		}

		widgets = {
			'username': forms.TextInput(attrs={
				'class': 'form-control',
				'placeholder': 'Nombre de usuario'
			}),

			'email': forms.EmailInput(attrs={
				'class': 'form-control',
				'placeholder': 'correo@ejemplo.com'
			}),

			'first_name': forms.TextInput(attrs={
				'class': 'form-control',
				'placeholder': 'Tu nombre'
			}),

			'last_name': forms.TextInput(attrs={
				'class': 'form-control',
				'placeholder': 'Tus apellidos'
			}),
		}

class CambiarPasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control'
            })

class CrearUsuarioForm(forms.ModelForm):

	password1 = forms.CharField(
		label='Contraseña',
		widget=forms.PasswordInput(attrs={
			'class': 'form-control'
		})
	)

	password2 = forms.CharField(
		label='Confirmar contraseña',
		widget=forms.PasswordInput(attrs={
			'class': 'form-control'
		})
	)

	rol = forms.ModelChoiceField(
		queryset=Group.objects.filter(
			name__in=['Administrador', 'Empleado']
		),
		label='Rol',
		empty_label=None,
		widget=forms.Select(attrs={
			'class': 'form-select'
		})
	)


	class Meta:

		model = User

		fields = (
			'username',
			'email',
			'first_name',
			'last_name',
			'rol',
		)

		labels = {
			'username': 'Nombre de usuario',
			'email': 'Correo electrónico',
			'first_name': 'Nombre',
			'last_name': 'Apellidos',
		}

		widgets = {

			'username': forms.TextInput(attrs={
				'class': 'form-control',
				'placeholder': 'Nombre de usuario'
			}),

			'email': forms.EmailInput(attrs={
				'class': 'form-control',
				'placeholder': 'correo@ejemplo.com'
			}),

			'first_name': forms.TextInput(attrs={
				'class': 'form-control',
				'placeholder': 'Nombre'
			}),

			'last_name': forms.TextInput(attrs={
				'class': 'form-control',
				'placeholder': 'Apellidos'
			}),
		}


	def clean(self):

		cleaned_data = super().clean()

		password1 = cleaned_data.get('password1')
		password2 = cleaned_data.get('password2')

		if password1 and password2 and password1 != password2:

			raise forms.ValidationError(
				'Las contraseñas no coinciden.'
			)

		return cleaned_data


	def save(self, commit=True):

		user = super().save(commit=False)

		user.set_password(
			self.cleaned_data['password1']
		)

		if commit:

			user.save()

			rol = self.cleaned_data['rol']

			user.groups.set([rol])

		return user

class EditarUsuarioAdminForm(forms.ModelForm):

	rol = forms.ModelChoiceField(
		queryset=Group.objects.filter(
			name__in=['Administrador', 'Empleado']
		),
		label='Rol',
		empty_label=None,
		widget=forms.Select(attrs={
			'class': 'form-select'
		})
	)


	class Meta:

		model = User

		fields = (
			'username',
			'email',
			'first_name',
			'last_name',
			'is_active',
			'rol',
		)

		labels = {
			'username': 'Nombre de usuario',
			'email': 'Correo electrónico',
			'first_name': 'Nombre',
			'last_name': 'Apellidos',
			'is_active': 'Cuenta activa',
		}

		widgets = {

			'username': forms.TextInput(attrs={
				'class': 'form-control'
			}),

			'email': forms.EmailInput(attrs={
				'class': 'form-control'
			}),

			'first_name': forms.TextInput(attrs={
				'class': 'form-control'
			}),

			'last_name': forms.TextInput(attrs={
				'class': 'form-control'
			}),

			'is_active': forms.CheckboxInput(attrs={
				'class': 'form-check-input'
			}),
		}


	def __init__(self, *args, **kwargs):

		super().__init__(*args, **kwargs)

		if self.instance.pk:

			grupo = self.instance.groups.filter(
				name__in=['Administrador', 'Empleado']
			).first()

			if grupo:

				self.fields['rol'].initial = grupo.pk

