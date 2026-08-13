import os
import uuid
from django.core.paginator import Paginator
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
try:
    from PIL import Image
except Exception:
    Image = None

from productos.models import Producto
from .forms import ProveedorForm
from .models import Gasto, GastoItem, GastoBonificacion, Proveedor
from django.http import JsonResponse


@login_required
def nuevo_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor registrado correctamente.')
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm()

    return render(request, 'nuevoProveedor.html', {'form': form, 'editar': False})


@login_required
def lista_proveedores(request):
    proveedores = Proveedor.objects.filter(activo=True)
    paginator = Paginator(proveedores, 10)  # Mostrar 14 proveedores por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'listaProveedor.html', {'proveedores': page_obj, 'page_obj': page_obj})


@login_required
def editar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado correctamente.')
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm(instance=proveedor)

    return render(request, 'nuevoProveedor.html', {'form': form, 'editar': True, 'proveedor': proveedor})


@login_required
def eliminar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.activo = False
        proveedor.save()
        messages.success(request, 'Proveedor eliminado correctamente.')
    return redirect('lista_proveedores')


@login_required
def registrar_gastos(request):
    proveedores = Proveedor.objects.filter(activo=True).order_by('nombre')
    productos = Producto.objects.order_by('nombre')

    if request.method == 'POST':
        proveedor_id = request.POST.get('proveedor')
        tipo_compra = request.POST.get('tipo_compra', 'efectivo')
        descripcion = request.POST.get('descripcion', '').strip()
        percepcion_raw = request.POST.get('percepcion', '0')

        if not proveedor_id:
            messages.warning(request, 'Selecciona un proveedor para registrar el gasto.')
            return render(request, 'registrarGastos.html', {
                'proveedores': proveedores,
                'productos': productos,
            })

        proveedor = get_object_or_404(Proveedor, pk=proveedor_id)
        items = []
        total = Decimal('0.00')
        try:
            percepcion = Decimal(percepcion_raw)
            if percepcion < 0:
                percepcion = Decimal('0.00')
        except Exception:
            percepcion = Decimal('0.00')

        for producto in productos:
            cantidad = request.POST.get(f'cantidad_{producto.pk}')
            costo = request.POST.get(f'costo_{producto.pk}')
            if not cantidad or not costo:
                continue

            try:
                if producto.unidadMedida and producto.unidadMedida.lower() in ('kilo', 'kg'):
                    cantidad_val = Decimal(cantidad)
                else:
                    cantidad_val = Decimal(int(cantidad))
                costo_val = Decimal(costo)
            except (ValueError, TypeError, InvalidOperation):
                continue

            if cantidad_val <= 0:
                continue

            subtotal = costo_val * cantidad_val
            total += subtotal
            items.append({
                'producto': producto,
                'cantidad': cantidad_val,
                'costo': costo_val,
                'subtotal': subtotal,
            })

        # procesar productos de bonificación (no suman al total, solo actualizan stock)
        bonos = []
        for producto in productos:
            cantidad_bono = request.POST.get(f'cantidad_bono_{producto.pk}')
            if not cantidad_bono:
                continue
            try:
                cantidad_bono_val = int(cantidad_bono)
            except (ValueError, TypeError):
                continue
            if cantidad_bono_val <= 0:
                continue
            bonos.append({'producto': producto, 'cantidad': cantidad_bono_val})

        if not items and percepcion == Decimal('0.00'):
            messages.warning(request, 'Debes elegir al menos un producto o ingresar una percepción mayor que cero.')
            return render(request, 'registrarGastos.html', {
                'proveedores': proveedores,
                'productos': productos,
            })

        codigo = f"GASTO-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        gasto = Gasto.objects.create(
            codigo=codigo,
            proveedor=proveedor,
            user=request.user,
            tipo_compra=tipo_compra,
            total=total + percepcion,
            percepcion=percepcion,
            descripcion=descripcion,
        )

        # Procesar imagen adjunta: comprimir y guardar en gasto.imagen
        image_file = request.FILES.get('image')

        if image_file:
            try:
                # Asegurar que el directorio de boletas exista
                os.makedirs(gasto.boletas_storage.location, exist_ok=True)
                if Image:
                    img = Image.open(image_file)
                    # Convertir a RGB si es necesario
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    # Redimensionar si es muy grande (max 1600 px)
                    max_size = (1600, 1600)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)

                    output = BytesIO()
                    img.save(output, format='JPEG', quality=70)
                    output.seek(0)

                    uploaded_image = InMemoryUploadedFile(
                        file=output,
                        field_name='image',
                        name=f"gasto_{gasto.pk}.jpg",
                        content_type='image/jpeg',
                        size=output.getbuffer().nbytes,
                        charset=None,
                    )
                    gasto.imagen.save(uploaded_image.name, uploaded_image, save=True)
                else:
                    # Pillow no disponible: guardar archivo tal cual
                    gasto.imagen.save(image_file.name, image_file, save=True)
            except Exception as e:
                messages.warning(request, f"No se pudo procesar la imagen: {e}")

        for item in items:
            producto = item['producto']
            GastoItem.objects.create(
                gasto=gasto,
                producto=producto,
                cantidad=item['cantidad'],
                costo=item['costo'],
                subtotal=item['subtotal'],
            )
            producto.stock += item['cantidad']
            producto.costo = item['costo']
            producto.save()

        for bono in bonos:
            GastoBonificacion.objects.create(
                gasto=gasto,
                producto=bono['producto'],
                cantidad=bono['cantidad'],
            )
            producto = bono['producto']
            producto.stock += bono['cantidad']
            producto.save()

        messages.success(request, 'Gasto registrado y stock actualizado correctamente.')
        return redirect('registrar_gastos')

    return render(request, 'registrarGastos.html', {
        'proveedores': proveedores,
        'productos': productos,
    })


@login_required
def cotizacion(request):
    return render(request, 'cotizacion.html')


@login_required
def lista_gastos(request):
    gastos = Gasto.objects.select_related('proveedor').order_by('-fecha')
    proveedor = request.GET.get('proveedor')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if proveedor:
        gastos = gastos.filter(proveedor__nombre__icontains=proveedor)
    
    if fecha_inicio:
        gastos = gastos.filter(fecha__date__gte=fecha_inicio)
    
    if fecha_fin:
        gastos = gastos.filter(fecha__date__lte=fecha_fin)
    
    paginator = Paginator(gastos, 14)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    
    return render(request, 'listaGastos.html', {
        'gastos': page_obj,
        'page_obj': page_obj,
        'proveedor': proveedor,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    })

                


@login_required
def detalle_gasto(request, pk):
    gasto = get_object_or_404(Gasto, pk=pk)
    return render(request, 'detalle_gasto.html', {'gasto': gasto})


@login_required
def buscar_productos(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse([], safe=False)

    productos = Producto.objects.filter(nombre__icontains=q).order_by('nombre')[:12]
    results = []
    for p in productos:
        results.append({
            'id': p.pk,
            'nombre': p.nombre,
            'stock': p.stock,
            'costo': str(p.costo),
            'precio': str(p.precio),
            'unidadMedida': p.unidadMedida,
        })

    return JsonResponse(results, safe=False)

