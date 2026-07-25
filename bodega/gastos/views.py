import uuid
from django.core.paginator import Paginator
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

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
    return render(request, 'listaProveedor.html', {'proveedores': proveedores})


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
    proveedores = Proveedor.objects.filter(activo=True)
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
                cantidad_val = int(cantidad)
                costo_val = Decimal(costo)
            except (ValueError, TypeError):
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
def lista_gastos(request):
    gastos = Gasto.objects.order_by('-fecha')

    paginator = Paginator(gastos, 14)  # Mostrar 14 gastos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'listaGastos.html', {'page_obj': page_obj, 'gastos': page_obj})


@login_required
def detalle_gasto(request, pk):
    gasto = get_object_or_404(Gasto, pk=pk)
    return render(request, 'detalle_gasto.html', {'gasto': gasto})


@login_required
def buscar_productos(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse([], safe=False)

    productos = Producto.objects.filter(nombre__icontains=q)[:12]
    results = []
    for p in productos:
        results.append({
            'id': p.pk,
            'nombre': p.nombre,
            'stock': p.stock,
            'costo': str(p.costo),
        })

    return JsonResponse(results, safe=False)

