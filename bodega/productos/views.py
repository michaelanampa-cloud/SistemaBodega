from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from decimal import Decimal
import datetime
from django.utils import timezone

from .models import Producto
from .forms import ProductoForm
from gastos.models import GastoItem

from django.contrib.auth.decorators import login_required

import os
from io import BytesIO

from PIL import Image, ImageOps

from django.conf import settings
from django.utils.text import slugify

from django.core.files.base import ContentFile


def _resolver_ruta_codigo_barras(producto):
    if producto.codigo_barras_imagen:
        ruta = os.path.join(settings.BASE_DIR, 'static', producto.codigo_barras_imagen.replace('/', os.sep))
        if os.path.exists(ruta):
            return ruta

    carpeta = os.path.join(settings.BASE_DIR, 'static', 'img', 'codigos_barra')
    os.makedirs(carpeta, exist_ok=True)
    nombre_archivo = f'codigo_{producto.pk or producto.codigo_barras}.png'
    ruta = os.path.join(carpeta, nombre_archivo)

    try:
        from barcode import Code128
        from barcode.writer import ImageWriter
        codigo = Code128(str(producto.codigo_barras), writer=ImageWriter())
        codigo.save(ruta.replace('.png', ''), options={
            'write_text': True,
            'text_distance': 4,
            'module_height': 13,
            'module_width': 1.8,
            'quiet_zone': 6,
            'font_size': 12,
        })
        producto.codigo_barras_imagen = f'img/codigos_barra/{nombre_archivo}'
        producto.save(update_fields=['codigo_barras_imagen'])
    except Exception:
        if not os.path.exists(ruta):
            ruta = ''

    return ruta if os.path.exists(ruta) else ''


def _obtener_ids_seleccionados(request):
    ids = request.session.get('productos_seleccionados', [])
    seleccionados = []
    for item in ids:
        try:
            seleccionados.append(int(item))
        except (TypeError, ValueError):
            continue
    return seleccionados


def _guardar_ids_seleccionados(request, ids):
    seleccionados = []
    vistos = set()
    for item in ids:
        try:
            valor = int(item)
        except (TypeError, ValueError):
            continue
        if valor not in vistos:
            seleccionados.append(valor)
            vistos.add(valor)
    request.session['productos_seleccionados'] = seleccionados
    request.session.modified = True
    return seleccionados


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
            archivo_imagen = form.cleaned_data.get('archivo_imagen')
            nombre_imagen = form.cleaned_data.get('nombre_imagen', '').strip()
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
                    formato = (imagen.format or 'JPEG').upper()
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
                    carpeta_productos = os.path.join(settings.BASE_DIR, 'static', 'img', 'productos')
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
                    with open(ruta_archivo, 'wb'
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
                    print('====================================')
                    print('IMAGEN GUARDADA EN:')
                    print(ruta_archivo)
                    print('NOMBRE GUARDADO EN BD:')
                    print(producto.imagen)
                    print('====================================')
                except Exception as e:
                    messages.error(request, f'Error al guardar la imagen: {e}')
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
            return redirect('lista_productos')
    else:
        form = ProductoForm()
    return render(
        request, 'productos/registros_productos.html',
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
	productos_seleccionados_ids = _obtener_ids_seleccionados(request)
	productos_seleccionados = list(Producto.objects.filter(pk__in=productos_seleccionados_ids).order_by('nombre'))

	return render(request, 'productos/lista_productos.html', {
		'page_obj': page_obj,
		'query': query,
		'tipo': tipo,
		'tipos_disponibles': tipos_disponibles,
		'productos_seleccionados': productos_seleccionados,
		'productos_seleccionados_ids': productos_seleccionados_ids,
		'vista_seleccionados': False,
		'total_seleccionados': len(productos_seleccionados),
	})


def productos_seleccionados(request):
    ids = _obtener_ids_seleccionados(request)
    productos = list(Producto.objects.filter(pk__in=ids).order_by('nombre'))
    paginator = Paginator(productos, 14)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'productos/lista_productos.html', {
        'page_obj': page_obj,
        'query': '',
        'tipo': '',
        'tipos_disponibles': Producto.objects.values_list('tipoProducto', flat=True).distinct().order_by('tipoProducto'),
        'productos_seleccionados': productos,
        'productos_seleccionados_ids': ids,
        'vista_seleccionados': True,
        'total_seleccionados': len(productos),
    })


def guardar_seleccion_productos(request):
    if request.method != 'POST':
        return redirect('lista_productos')

    producto_id = request.POST.get('producto_id')
    accion = request.POST.get('accion', 'agregar')
    ids = _obtener_ids_seleccionados(request)

    if accion == 'limpiar':
        ids = []
    elif producto_id:
        try:
            producto_id = int(producto_id)
        except ValueError:
            return JsonResponse({'ok': False, 'error': 'id inválido'}, status=400)

        if accion == 'agregar' and producto_id not in ids:
            ids.append(producto_id)
        elif accion == 'quitar' and producto_id in ids:
            ids.remove(producto_id)

    ids = _guardar_ids_seleccionados(request, ids)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
        return JsonResponse({'ok': True, 'total': len(ids)})

    messages.success(request, 'Selección actualizada.')
    return redirect('lista_productos')


def toggle_oferta_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method != 'POST':
        return redirect('lista_productos')

    producto.en_oferta = not producto.en_oferta
    if producto.en_oferta:
        producto.descuento_oferta = Decimal('10.00')
        messages.success(request, f'Producto agregado a ofertas: {producto.nombre}')
    else:
        producto.descuento_oferta = Decimal('0.00')
        messages.info(request, f'Producto quitado de ofertas: {producto.nombre}')
    producto.save(update_fields=['en_oferta', 'descuento_oferta'])
    return redirect('lista_productos')


def ofertas_productos(request):
    productos = Producto.objects.filter(en_oferta=True).order_by('-created_at')
    return render(request, 'productos/ofertas_productos.html', {
        'page_obj': productos,
        'productos': productos,
    })

@login_required
def detalle_producto(request, pk):

    producto = get_object_or_404(Producto, pk=pk)

    ultima_compra = (
    GastoItem.objects
    .filter(producto=producto)
    .select_related('gasto', 'gasto__proveedor')
    .order_by('-gasto__fecha')
    .first()
    )

    historial_compras = (
        GastoItem.objects
        .filter(producto=producto)
        .select_related('gasto', 'gasto__proveedor')
        .order_by('-gasto__fecha')[:5]
    )

    return render(request, 'productos/detalle_producto.html', {
        'producto': producto,
        'ultima_compra': ultima_compra,
        'historial_compras': historial_compras,
    })

def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(
            request.POST,
            request.FILES,
            instance=producto
        )
        if form.is_valid():
            producto_editado = form.save(commit=False)
            archivo_imagen = form.cleaned_data.get('archivo_imagen')
            nombre_imagen = form.cleaned_data.get('nombre_imagen', '').strip()
            # ==================================================
            # SI SE SELECCIONÓ UNA NUEVA IMAGEN
            # ==================================================
            if archivo_imagen:
                try:
                    # ------------------------------------------
                    # ABRIR IMAGEN
                    # ------------------------------------------
                    imagen = Image.open(archivo_imagen)
                    # ------------------------------------------
                    # CORREGIR ORIENTACIÓN
                    # ------------------------------------------
                    imagen = ImageOps.exif_transpose(imagen)
                    # ------------------------------------------
                    # DETERMINAR FORMATO
                    # ------------------------------------------
                    formato = (imagen.format or 'JPEG').upper()
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
                    imagen.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
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
                    messages.error(request, f'Error al actualizar la imagen: {e}')
                    return render(request, 'productos/editar_producto.html',
                        {
                            'form': form,
                            'producto': producto
                        }
                    )
            if not producto_editado.codigo_barras:
                producto_editado.codigo_barras = producto_editado._generar_codigo_barras()
            # ==================================================
            # GUARDAR PRODUCTO
            # ==================================================
            producto_editado.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('lista_productos')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'productos/editar_producto.html',
        {
            'form': form,
            'producto': producto
        }
    )


def _dibujar_etiqueta_adhesiva(pdf, producto, x, y, ancho=220, alto=120):
    pdf.setStrokeColorRGB(0.2, 0.2, 0.2)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.rect(x, y, ancho, alto, stroke=1, fill=1)

    pdf.setFont('Helvetica-Bold', 11)
    pdf.setFillColorRGB(0, 0, 0)
    titulo = producto.nombre[:28]
    pdf.drawString(x + 8, y + alto - 18, titulo)

    pdf.setFont('Helvetica', 9)
    pdf.drawString(x + 8, y + alto - 34, f'Tipo: {producto.tipoProducto}')
    pdf.drawString(x + 8, y + alto - 48, f'Precio: S/ {producto.precio}')

    ruta_barra = _resolver_ruta_codigo_barras(producto)
    if ruta_barra and os.path.exists(ruta_barra):
        pdf.drawImage(ruta_barra, x + 8, y + 18, width=ancho - 16, height=42)

    pdf.setFont('Helvetica-Bold', 9)
    pdf.drawString(x + 12, y + 8, str(producto.codigo_barras))
    pdf.setFont('Helvetica', 7)
    pdf.drawString(x + 8, y + 2, 'Bodega Doña Catita')


def imprimir_etiqueta_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        messages.error(request, 'Falta instalar reportlab o python-barcode en el entorno del proyecto.')
        return redirect('detalle_producto', pk=pk)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="etiqueta_{producto.pk}.pdf"'

    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=A4)
    pdf.setTitle(f'Etiqueta {producto.nombre}')
    _dibujar_etiqueta_adhesiva(pdf, producto, 50, 540, ancho=240, alto=140)
    pdf.save()

    pdf_buffer.seek(0)
    response.write(pdf_buffer.getvalue())
    return response


def imprimir_etiquetas_productos(request):
    if request.method != 'POST':
        return redirect('lista_productos')

    ids = request.POST.getlist('producto_ids')
    if not ids:
        ids = _obtener_ids_seleccionados(request)
    productos = list(Producto.objects.filter(pk__in=ids).order_by('nombre')) if ids else []

    if not productos:
        messages.warning(request, 'Selecciona al menos un producto para imprimir sus etiquetas.')
        return redirect('lista_productos')

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        messages.error(request, 'Falta instalar reportlab en el entorno del proyecto.')
        return redirect('lista_productos')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="etiquetas_seleccionadas.pdf"'

    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=A4)
    pdf.setTitle('Etiquetas de productos seleccionados')

    posiciones = [
        (40, 720), (290, 720),
        (40, 520), (290, 520),
        (40, 320), (290, 320),
    ]

    for idx, producto in enumerate(productos):
        if idx and idx % 6 == 0:
            pdf.showPage()
        x, y = posiciones[idx % 6]
        _dibujar_etiqueta_adhesiva(pdf, producto, x, y, ancho=200, alto=120)

    pdf.save()
    pdf_buffer.seek(0)
    response.write(pdf_buffer.getvalue())
    return response

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

def productos_stock(request):
    stock_maximo = request.GET.get('stock', '5')
    try:
        stock_maximo = float(stock_maximo)
    except (ValueError, TypeError):
        stock_maximo = 5
    # Kilo: stock menor a 0.5
    # Otras unidades: stock menor o igual a 5
    productos = Producto.objects.filter(
        Q(unidadMedida__iexact='Kilo', stock__lt=0.5) |
        Q(~Q(unidadMedida__iexact='Kilo'), stock__lte=stock_maximo)
    ).order_by('stock', 'nombre')
    paginator = Paginator(productos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        'productos/productos_stock.html',
        {
            'page_obj': page_obj,
            'stock_maximo': stock_maximo,
        }
    )