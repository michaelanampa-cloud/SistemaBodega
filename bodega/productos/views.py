from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q
import datetime
from django.utils import timezone

from .models import Producto
from .forms import ProductoForm

from django.contrib.auth.decorators import login_required

import os
from io import BytesIO

from PIL import Image, ImageOps

from django.conf import settings
from django.utils.text import slugify

from django.core.files.base import ContentFile

def registros_productos(request):

    if not request.user.has_perm('productos.add_producto'):
        messages.error(
            request,
            'No tienes permisos para registrar nuevos productos.'
        )
        return redirect('lista_productos')

    if request.method == 'POST':

        # IMPORTANTE:
        # request.FILES permite recibir la fotografía
        form = ProductoForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            producto = form.save(commit=False)

            archivo_imagen = form.cleaned_data.get(
                'archivo_imagen'
            )

            nombre_imagen = form.cleaned_data.get(
                'nombre_imagen',
                ''
            ).strip()

            # ==========================================
            # SI SE SELECCIONÓ UNA IMAGEN
            # ==========================================

            if archivo_imagen:

                try:

                    import os
                    from io import BytesIO

                    from PIL import Image, ImageOps
                    from django.conf import settings
                    from django.utils.text import slugify


                    # ==================================
                    # ABRIR IMAGEN
                    # ==================================

                    imagen = Image.open(
                        archivo_imagen
                    )


                    # Corregir orientación de fotos
                    # tomadas desde celular
                    imagen = ImageOps.exif_transpose(
                        imagen
                    )


                    # ==================================
                    # DETERMINAR FORMATO
                    # ==================================

                    formato = (
                        imagen.format or 'JPEG'
                    ).upper()


                    if formato == 'PNG':

                        extension = '.png'

                    elif formato in ['JPEG', 'JPG']:

                        extension = '.jpg'

                    elif formato == 'WEBP':

                        extension = '.webp'

                    else:

                        # Otros formatos los convertimos
                        # a JPG
                        extension = '.jpg'


                    # ==================================
                    # PREPARAR IMAGEN
                    # ==================================

                    if extension == '.jpg':

                        if imagen.mode != 'RGB':
                            imagen = imagen.convert('RGB')

                    elif extension == '.png':

                        if imagen.mode not in [
                            'RGB',
                            'RGBA'
                        ]:
                            imagen = imagen.convert('RGBA')


                    elif extension == '.webp':

                        if imagen.mode != 'RGB':
                            imagen = imagen.convert('RGB')


                    # ==================================
                    # REDUCIR DIMENSIONES
                    # ==================================

                    imagen.thumbnail(
                        (1200, 1200),
                        Image.Resampling.LANCZOS
                    )


                    # ==================================
                    # NOMBRE DE LA IMAGEN
                    # ==================================

                    if nombre_imagen:

                        # Si escribió:
                        # arroz-costeno.png
                        #
                        # quitamos .png
                        nombre_base = os.path.splitext(
                            nombre_imagen
                        )[0]

                    else:

                        nombre_base = producto.nombre


                    # Convertir a nombre seguro
                    nombre_base = slugify(
                        nombre_base
                    )


                    if not nombre_base:

                        nombre_base = 'producto'


                    # ==================================
                    # CARPETA DE DESTINO
                    # ==================================

                    carpeta_productos = os.path.join(
                        settings.BASE_DIR,
                        'static',
                        'img',
                        'productos'
                    )


                    # Crear carpeta si no existe
                    os.makedirs(
                        carpeta_productos,
                        exist_ok=True
                    )


                    # ==================================
                    # NOMBRE FINAL
                    # ==================================

                    nombre_archivo = (
                        f'{nombre_base}{extension}'
                    )


                    ruta_archivo = os.path.join(
                        carpeta_productos,
                        nombre_archivo
                    )


                    # ==================================
                    # EVITAR SOBRESCRIBIR
                    # ==================================

                    contador = 1

                    while os.path.exists(
                        ruta_archivo
                    ):

                        nombre_archivo = (
                            f'{nombre_base}-{contador}'
                            f'{extension}'
                        )

                        ruta_archivo = os.path.join(
                            carpeta_productos,
                            nombre_archivo
                        )

                        contador += 1


                    # ==================================
                    # COMPRIMIR
                    # ==================================

                    buffer = BytesIO()


                    if extension == '.jpg':

                        imagen.save(
                            buffer,
                            format='JPEG',
                            quality=80,
                            optimize=True
                        )


                    elif extension == '.png':

                        imagen.save(
                            buffer,
                            format='PNG',
                            optimize=True
                        )


                    elif extension == '.webp':

                        imagen.save(
                            buffer,
                            format='WEBP',
                            quality=80,
                            method=6
                        )


                    # ==================================
                    # GUARDAR ARCHIVO
                    # ==================================

                    with open(
                        ruta_archivo,
                        'wb'
                    ) as archivo:

                        archivo.write(
                            buffer.getvalue()
                        )


                    # ==================================
                    # GUARDAR NOMBRE EN BASE DE DATOS
                    # ==================================

                    producto.imagen = nombre_archivo


                    # ==================================
                    # INFORMACIÓN PARA COMPROBAR
                    # ==================================
                    print(
                        '===================================='
                    )
                    print(
                        'IMAGEN GUARDADA EN:'
                    )
                    print(
                        ruta_archivo
                    )
                    print(
                        'NOMBRE GUARDADO EN BD:'
                    )
                    print(
                        producto.imagen
                    )
                    print(
                        '===================================='
                    )
                except Exception as e:
                    messages.error(
                        request,
                        f'Error al guardar la imagen: {e}'
                    )
                    return render(
                        request,
                        'productos/registros_productos.html',
                        {
                            'form': form
                        }
                    )

            # ==========================================
            # GUARDAR PRODUCTO
            # ==========================================
            producto.save()
            messages.success(
                request,
                'Producto creado correctamente.'
            )
            return redirect(
                'lista_productos'
            )
    else:
        form = ProductoForm()
    return render(
        request,
        'productos/registros_productos.html',
        {
            'form': form
        }
    )

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
    producto = get_object_or_404(
        Producto,
        pk=pk
    )
    if request.method == 'POST':
        form = ProductoForm(
            request.POST,
            request.FILES,
            instance=producto
        )
        if form.is_valid():
            producto_editado = form.save(
                commit=False
            )
            archivo_imagen = form.cleaned_data.get(
                'archivo_imagen'
            )
            nombre_imagen = form.cleaned_data.get(
                'nombre_imagen',
                ''
            ).strip()
            # ==================================================
            # SI SE SELECCIONÓ UNA NUEVA IMAGEN
            # ==================================================
            if archivo_imagen:
                try:
                    # ------------------------------------------
                    # ABRIR IMAGEN
                    # ------------------------------------------
                    imagen = Image.open(
                        archivo_imagen
                    )
                    # ------------------------------------------
                    # CORREGIR ORIENTACIÓN
                    # ------------------------------------------
                    imagen = ImageOps.exif_transpose(
                        imagen
                    )
                    # ------------------------------------------
                    # DETERMINAR FORMATO
                    # ------------------------------------------
                    formato = (
                        imagen.format or 'JPEG'
                    ).upper()
                    if formato == 'PNG':
                        extension = '.png'
                    elif formato in ['JPEG', 'JPG']:
                        extension = '.jpg'
                    elif formato == 'WEBP':
                        extension = '.webp'
                    else:
                        extension = '.jpg'
                    # ------------------------------------------
                    # PREPARAR IMAGEN
                    # ------------------------------------------
                    if extension == '.jpg':
                        if imagen.mode != 'RGB':
                            imagen = imagen.convert(
                                'RGB'
                            )
                    elif extension == '.png':
                        if imagen.mode not in [
                            'RGB',
                            'RGBA'
                        ]:
                            imagen = imagen.convert(
                                'RGBA'
                            )
                    elif extension == '.webp':
                        if imagen.mode != 'RGB':
                            imagen = imagen.convert(
                                'RGB'
                            )
                    # ------------------------------------------
                    # REDUCIR DIMENSIONES
                    # ------------------------------------------
                    imagen.thumbnail(
                        (1200, 1200),
                        Image.Resampling.LANCZOS
                    )
                    # ------------------------------------------
                    # NOMBRE DE IMAGEN
                    # ------------------------------------------
                    if nombre_imagen:
                        nombre_base = os.path.splitext(
                            nombre_imagen
                        )[0]
                    else:

                        nombre_base = producto.nombre
                    nombre_base = slugify(
                        nombre_base
                    )
                    if not nombre_base:

                        nombre_base = 'producto'
                    # ------------------------------------------
                    # CARPETA
                    # ------------------------------------------
                    carpeta_productos = os.path.join(
                        settings.BASE_DIR,
                        'static',
                        'img',
                        'productos'
                    )
                    os.makedirs(
                        carpeta_productos,
                        exist_ok=True
                    )
                    # ------------------------------------------
                    # NOMBRE FINAL
                    # ------------------------------------------
                    nombre_archivo = (
                        f'{nombre_base}{extension}'
                    )
                    ruta_archivo = os.path.join(
                        carpeta_productos,
                        nombre_archivo
                    )
                    # ------------------------------------------
                    # EVITAR SOBRESCRIBIR
                    # ------------------------------------------
                    contador = 1
                    while os.path.exists(
                        ruta_archivo
                    ):
                        nombre_archivo = (
                            f'{nombre_base}-'
                            f'{contador}'
                            f'{extension}'
                        )
                        ruta_archivo = os.path.join(
                            carpeta_productos,
                            nombre_archivo
                        )
                        contador += 1
                    # ------------------------------------------
                    # COMPRIMIR
                    # ------------------------------------------
                    buffer = BytesIO()
                    if extension == '.jpg':
                        imagen.save(
                            buffer,
                            format='JPEG',
                            quality=80,
                            optimize=True
                        )
                    elif extension == '.png':
                        imagen.save(
                            buffer,
                            format='PNG',
                            optimize=True
                        )
                    elif extension == '.webp':
                        imagen.save(
                            buffer,
                            format='WEBP',
                            quality=80,
                            method=6
                        )
                    # ------------------------------------------
                    # GUARDAR NUEVA IMAGEN
                    # ------------------------------------------
                    with open(
                        ruta_archivo,
                        'wb'
                    ) as archivo:
                        archivo.write(
                            buffer.getvalue()
                        )
                    # ------------------------------------------
                    # IMAGEN ANTERIOR
                    # ------------------------------------------
                    imagen_anterior = producto.imagen
                    # ------------------------------------------
                    # GUARDAR NOMBRE EN EL PRODUCTO
                    # ------------------------------------------
                    producto_editado.imagen = (
                        nombre_archivo
                    )
                    # ------------------------------------------
                    # ELIMINAR IMAGEN ANTERIOR
                    # ------------------------------------------
                    if imagen_anterior:
                        ruta_anterior = os.path.join(
                            carpeta_productos,
                            imagen_anterior
                        )
                        if os.path.exists(
                            ruta_anterior
                        ):
                            try:
                                os.remove(
                                    ruta_anterior
                                )
                            except OSError:
                                pass
                except Exception as e:
                    messages.error(
                        request,
                        f'Error al actualizar la imagen: {e}'
                    )
                    return render(
                        request,
                        'productos/editar_producto.html',
                        {
                            'form': form,
                            'producto': producto
                        }
                    )
            # ==================================================
            # GUARDAR PRODUCTO
            # ==================================================
            producto_editado.save()
            messages.success(
                request,
                'Producto actualizado correctamente.'
            )
            return redirect(
                'lista_productos'
            )
    else:

        form = ProductoForm(
            instance=producto
        )
    return render(
        request,
        'productos/editar_producto.html',
        {
            'form': form,
            'producto': producto
        }
    )

def eliminar_producto(request, pk):
	producto = get_object_or_404(Producto, pk=pk)
	if request.method == 'POST':
		producto.delete()
		messages.success(request, 'Producto eliminado.')
		return redirect('lista_productos')
	return render(request, 'productos/eliminar_producto.html', {'producto': producto})

def productos_vencer(request):
	"""Muestra productos con fecha de vencimiento próxima (por defecto 7 días) y permite buscar por fecha exacta."""
	fecha_str = request.GET.get('fecha', '').strip()
	hoy = timezone.now().date()
	hasta = hoy + datetime.timedelta(days=7)
	productos = Producto.objects.filter(fechaVencimiento__isnull=False)

	if fecha_str:
		try:
			# Esperamos formato YYYY-MM-DD desde el input type=date
			fecha = datetime.datetime.strptime(fecha_str, '%Y-%m-%d').date()
			productos = productos.filter(fechaVencimiento=fecha).order_by('fechaVencimiento')
		except ValueError:
			messages.warning(request, 'Formato de fecha inválido. Usa YYYY-MM-DD.')
			productos = Producto.objects.none()
	else:
		# Por defecto mostrar productos ya vencidos o con vencimiento hasta los próximos 7 días
		productos = productos.filter(fechaVencimiento__lte=hasta).order_by('fechaVencimiento')

	paginator = Paginator(productos, 14)
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)

	return render(request, 'productos/productos_vencer.html', {
		'page_obj': page_obj,
		'fecha_busqueda': fecha_str,
		'hoy': hoy,
		'hasta': hasta,
	})
