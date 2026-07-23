from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q

from .models import Producto
from .forms import ProductoForm


def registros_productos(request):
	if request.method == 'POST':
		form = ProductoForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Producto creado correctamente.')
			return redirect('lista_productos')
	else:
		form = ProductoForm()
	return render(request, 'productos/registros_productos.html', {'form': form})


def lista_productos(request):
	query = request.GET.get('q', '').strip()
	tipo = request.GET.get('tipo', '').strip()
	productos = Producto.objects.all().order_by('-created_at')

	if query:
		productos = productos.filter(
			Q(nombre__icontains=query) | Q(detalle__icontains=query)
		)

	if tipo:
		productos = productos.filter(tipoProducto__iexact=tipo)

	tipos_disponibles = Producto.objects.values_list('tipoProducto', flat=True).distinct().order_by('tipoProducto')

	paginator = Paginator(productos, 14)  # Mostrar 14 productos por página
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)

	return render(request, 'productos/lista_productos.html', {
		'page_obj': page_obj,
		'query': query,
		'tipo': tipo,
		'tipos_disponibles': tipos_disponibles,
	})


def detalle_producto(request, pk):
	producto = get_object_or_404(Producto, pk=pk)
	return render(request, 'productos/detalle_producto.html', {'producto': producto})


def editar_producto(request, pk):
	producto = get_object_or_404(Producto, pk=pk)
	if request.method == 'POST':
		form = ProductoForm(request.POST, instance=producto)
		if form.is_valid():
			form.save()
			messages.success(request, 'Producto actualizado.')
			return redirect('lista_productos')
	else:
		form = ProductoForm(instance=producto)
	return render(request, 'productos/editar_producto.html', {'form': form, 'producto': producto})


def eliminar_producto(request, pk):
	producto = get_object_or_404(Producto, pk=pk)
	if request.method == 'POST':
		producto.delete()
		messages.success(request, 'Producto eliminado.')
		return redirect('lista_productos')
	return render(request, 'productos/eliminar_producto.html', {'producto': producto})
