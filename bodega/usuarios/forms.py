from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User


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
