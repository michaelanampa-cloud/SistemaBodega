import uuid
from decimal import Decimal
from io import BytesIO
from django.core.paginator import Paginator

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from productos.models import Producto
from clientes.models import Cliente
from .models import Compra, CompraItem
from django.http import JsonResponse


@login_required
def eliminar_carrito(request, pk):
    if request.method != 'POST':
        return redirect('carrito')

    carrito = _obtener_carrito(request)
    item_id = str(pk)
    if item_id in carrito:
        carrito.pop(item_id)
        _guardar_carrito(request, carrito)
        messages.success(request, 'Producto eliminado del carrito.')
    else:
        messages.warning(request, 'El producto no se encontró en el carrito.')

    return redirect('carrito')


def _obtener_carrito(request):
    return request.session.get('carrito', {})


def _guardar_carrito(request, carrito):
    request.session['carrito'] = carrito
    request.session.modified = True


@login_required
def agregar_carrito(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    cantidad = 1
    if request.method == 'POST':
        try:
            cantidad_str = request.POST.get('cantidad', '1')
            if producto.unidadMedida and producto.unidadMedida.lower() in ('kilo', 'kg'):
                cantidad = float(cantidad_str)
            else:
                cantidad = int(cantidad_str)
        except (ValueError, TypeError):
            cantidad = 1
    if cantidad < 1:
        cantidad = 1

    # Use Decimal for stock comparisons
    prod_stock = Decimal(str(producto.stock))
    cantidad_dec = Decimal(str(cantidad))
    if cantidad_dec > prod_stock:
        messages.error(request, f"No hay suficiente stock para {producto.nombre}.")
        return redirect('detalle_producto', pk=producto.pk)

    carrito = _obtener_carrito(request)
    item_id = str(producto.pk)
    cantidad_actual = carrito.get(item_id, None)
    cantidad_actual_dec = Decimal(str(cantidad_actual)) if cantidad_actual is not None else Decimal('0')
    nueva_cantidad = cantidad_actual_dec + cantidad_dec
    if nueva_cantidad > prod_stock:
        messages.error(request, f"No puedes agregar más de {producto.stock} unidades de {producto.nombre}.")
        return redirect('detalle_producto', pk=producto.pk)

    # Store as string to preserve exact decimal value in session
    carrito[item_id] = str(nueva_cantidad)
    _guardar_carrito(request, carrito)
    messages.success(request, f"{producto.nombre} fue agregado al carrito.")
    return redirect('carrito')


@login_required
def carrito_view(request):
    carrito = _obtener_carrito(request)
    items = []
    total = Decimal('0.00')

    for producto_id, cantidad in carrito.items():
        producto = get_object_or_404(Producto, pk=int(producto_id))
        cantidad = Decimal(str(cantidad))  # Convert to Decimal to avoid type mismatch
        subtotal = producto.precio * cantidad
        items.append({'producto': producto, 'cantidad': cantidad, 'subtotal': subtotal})
        total += subtotal

    return render(request, 'carrito.html', {'items': items, 'total': total})


@login_required
def actualizar_carrito(request):
    if request.method != 'POST':
        return redirect('carrito')

    carrito = _obtener_carrito(request)
    nuevo_carrito = {}

    for producto_id, cantidad in request.POST.items():
        if not producto_id.startswith('cantidad_'):
            continue
        try:
            pk = int(producto_id.replace('cantidad_', ''))
            producto = get_object_or_404(Producto, pk=pk)
            # Allow decimals for kilo-based products
            if producto.unidadMedida and producto.unidadMedida.lower() in ('kilo', 'kg'):
                cantidad = Decimal(str(cantidad))
            elif producto.unidadMedida and producto.unidadMedida.lower() in ('metro', 'm'):
                cantidad = Decimal(str(cantidad))
            else:
                cantidad = Decimal(int(cantidad))
        except (ValueError, TypeError):
            continue

        if cantidad <= 0:
            continue

        prod_stock = Decimal(str(producto.stock))
        if cantidad > prod_stock:
            messages.warning(request, f"Stock insuficiente para {producto.nombre}. Se ajustó al máximo disponible.")
            cantidad = prod_stock

        # store as string in session
        nuevo_carrito[str(pk)] = str(cantidad)

    _guardar_carrito(request, nuevo_carrito)
    messages.success(request, 'Carrito actualizado correctamente.')
    return redirect('carrito')


@login_required
def registrar_compra(request):
    carrito = _obtener_carrito(request)
    if not carrito:
        messages.warning(request, 'El carrito está vacío. Agrega productos antes de registrar la compra.')
        return redirect('carrito')

    items = []
    total = Decimal('0.00')

    for producto_id, cantidad in carrito.items():
        producto = get_object_or_404(Producto, pk=int(producto_id))
        cantidad = Decimal(str(cantidad))  # Convert to Decimal to avoid type mismatch
        prod_stock = Decimal(str(producto.stock))
        if cantidad > prod_stock:
            messages.error(request, f"No hay suficiente stock para {producto.nombre}.")
            return redirect('carrito')
        subtotal = producto.precio * cantidad
        items.append({'producto': producto, 'cantidad': cantidad, 'subtotal': subtotal})
        total += subtotal

    if request.method == 'POST':
        cliente_id = request.POST.get('cliente')
        tipo_compra = request.POST.get('tipo_compra', 'efectivo')
        descripcion = request.POST.get('descripcion', '').strip()
        try:
            descuento = Decimal(str(request.POST.get('descuento', '0')))
            adicional = Decimal(str(request.POST.get('adicional', '0')))
            dinero_recibido = Decimal(str(request.POST.get('dinero', '0')))
        except (ValueError, TypeError):
            descuento = Decimal('0.00')
            adicional = Decimal('0.00')
            dinero_recibido = Decimal('0.00')
        
        cliente = None
        if cliente_id:
            cliente = get_object_or_404(Cliente, pk=cliente_id)

        bolsa_producto_id = request.POST.get('bolsa_producto')
        bolsa_producto = None
        if bolsa_producto_id:
            bolsa_producto = get_object_or_404(Producto, pk=bolsa_producto_id, tipoProducto__iexact='Bolsas')
            if bolsa_producto.stock < Decimal('1'):
                messages.error(request, f"No hay suficiente stock para {bolsa_producto.nombre}.")
                return redirect('carrito')

        # Calcular total final
        total_final = total - descuento + adicional

        vuelto = Decimal('0.00')

        if tipo_compra == 'efectivo' and dinero_recibido > total_final:
            vuelto = dinero_recibido - total_final

        # Si el cliente es "FAMILIA", el total se vuelve 0 pero se registra la compra y
        # se descuenta el stock normalmente
        try:
            if cliente and cliente.nombre and cliente.nombre.strip().upper() == 'FAMILIA':
                total_final = Decimal('0.00')
        except Exception:
            # En caso de cualquier error no interrumpimos el flujo
            pass

        codigo = f"COMP-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        compra = Compra.objects.create(
            user=request.user, 
            cliente=cliente,
            codigo=codigo,
            subtotal=total,
            descuento=descuento,
            adicional=adicional,
            total=total_final,
            dinero_recibido=dinero_recibido,
            vuelto=vuelto,
            tipo_compra=tipo_compra,
            descripcion=descripcion,
        )

        if bolsa_producto:
            CompraItem.objects.create(
                compra=compra,
                producto=bolsa_producto,
                cantidad=Decimal('1'),
                precio=Decimal('0.00'),
                subtotal=Decimal('0.00'),
            )
            bolsa_producto.stock = Decimal(str(bolsa_producto.stock)) - Decimal('1')
            bolsa_producto.save()

        for item in items:
            producto = item['producto']
            CompraItem.objects.create(
                compra=compra,
                producto=producto,
                cantidad=item['cantidad'],
                precio=producto.precio,
                subtotal=item['subtotal'],
            )
            if producto.unidadMedida and producto.unidadMedida.lower() in ('kilo', 'kg'):
                producto.stock = Decimal(str(producto.stock)) - Decimal(str(item['cantidad']))
            else:
                producto.stock = Decimal(str(producto.stock)) - Decimal(int(item['cantidad']))
            producto.save()

        request.session['carrito'] = {}
        messages.success(request, 'Compra registrada correctamente.')
        return redirect('compra_detalle', pk=compra.pk)
    
    # GET: Mostrar formulario para seleccionar cliente y tipo de compra
    clientes = Cliente.objects.filter(activo=True)
    bolsas = Producto.objects.filter(tipoProducto__iexact='Bolsas')
    return render(request, 'compra.html', {
        'items': items, 
        'total': total,
        'clientes': clientes,
        'bolsas': bolsas,
        'es_formulario': True
    })


@login_required
def lista_compras(request):
    compras = Compra.objects.select_related('cliente').order_by('-fecha')
    cliente = request.GET.get('cliente')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if cliente:
        compras = compras.filter(cliente__nombre__icontains=cliente)

    if fecha_inicio:
        compras = compras.filter(fecha__date__gte=fecha_inicio)

    if fecha_fin:
        compras = compras.filter(fecha__date__lte=fecha_fin)

    paginator = Paginator(compras, 14)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    return render(request, 'lista_compras.html', {
        'compras': page_obj,
        'page_obj': page_obj,
        'cliente': cliente,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    })


@login_required
def compra_detalle(request, pk):
    compra = get_object_or_404(
        Compra.objects.select_related('cliente', 'user').prefetch_related(
            'items__producto'
        ),
        pk=pk
    )
    clientes = Cliente.objects.filter(activo=True)
    selected_cliente_id = None
    email_to = ''

    if request.method == 'POST':
        selected_cliente_id = request.POST.get('cliente')
        email_to = request.POST.get('email', '').strip()

        if selected_cliente_id:
            try:
                cliente = get_object_or_404(Cliente, pk=selected_cliente_id)
            except Http404:
                cliente = None
        else:
            cliente = None

        if cliente and cliente.email:
            email_to = cliente.email

        if not email_to:
            messages.error(request, 'Debes seleccionar un cliente con correo o ingresar un email para enviar la boleta.')
        else:
            subject = f'Boleta de compra {compra.codigo}'
            lines = [
                'Boleta de compra',
                'Bodega Doña Catita',
                'RUC: 1012038912',
                'Dirección: calle 3 de octubre 1598',
                '',
                f'Fecha: {compra.fecha.strftime("%d/%m/%Y %H:%M")}',
                f'Código: {compra.codigo}',
                f'Cliente: {compra.cliente.nombre if compra.cliente else "Sin cliente asignado"}',
                f'Tipo de compra: {compra.get_tipo_compra_display}',
                '',
                'Productos:',
            ]
            for item in compra.items.all():
                lines.append(
                    f'- {item.producto.nombre} | Costo unitario: S/ {item.precio:.2f} | Cantidad: {item.cantidad} | Subtotal: S/ {item.subtotal:.2f}'
                )
            lines += [
                '',
                f'Subtotal: S/ {compra.subtotal:.2f}',
            ]
            if compra.descuento:
                lines.append(f'Descuento: -S/ {compra.descuento:.2f}')
            if compra.adicional:
                lines.append(f'Adicional: +S/ {compra.adicional:.2f}')
            lines.append(f'Total: S/ {compra.total:.2f}')
            message = '\n'.join(lines)
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None) or 'no-reply@example.com'

            try:
                send_mail(subject, message, from_email, [email_to], fail_silently=False)
                messages.success(request, f'Boleta enviada correctamente a {email_to}.')
            except Exception as e:
                messages.error(request, f'Error al enviar el correo: {e}')

    return render(request, 'detalle_compra.html', {
        'compra': compra,
        'clientes': clientes,
        'selected_cliente_id': selected_cliente_id,
        'email_to': email_to,
    })


@login_required
def exportar_pdf(request, pk):
    compra = get_object_or_404(Compra, pk=pk)

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas
    except ImportError:
        messages.error(request, 'Para exportar PDF instala reportlab: pip install reportlab')
        return redirect('compra_detalle', pk=compra.pk)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle(f"Compra {compra.codigo}")
    pdf.setFont('Helvetica-Bold', 14)
    pdf.drawString(72, 750, f"Detalle de compra: {compra.codigo}")
    pdf.setFont('Helvetica', 11)
    pdf.drawString(72, 730, f"Fecha: {compra.fecha.strftime('%d/%m/%Y %H:%M')}")
    pdf.drawString(72, 715, f"Total: S/ {compra.total}")
    pdf.drawString(72, 700, f"Usuario: {compra.user or 'Anónimo'}")

    y = 680
    pdf.setFont('Helvetica-Bold', 11)
    pdf.drawString(72, y, 'Producto')
    pdf.drawString(280, y, 'Cantidad')
    pdf.drawString(360, y, 'Precio')
    pdf.drawString(440, y, 'Subtotal')
    pdf.setFont('Helvetica', 11)
    y -= 18

    for item in compra.items.all():
        if y < 72:
            pdf.showPage()
            y = 750
        pdf.drawString(72, y, item.producto.nombre)
        pdf.drawString(280, y, str(item.cantidad))
        pdf.drawString(360, y, f"S/ {item.precio}")
        pdf.drawString(440, y, f"S/ {item.subtotal}")
        y -= 18

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="compra_{compra.codigo}.pdf"'
    return response

@login_required
def actualizar_totales(request):
    if request.method == 'POST':
        carrito = _obtener_carrito(request)
        items = []
        total = Decimal('0.00')

        for producto_id, cantidad in carrito.items():
            producto = get_object_or_404(Producto, pk=int(producto_id))
            cantidad = Decimal(str(cantidad))  # Convert to Decimal to avoid type mismatch
            subtotal = producto.precio * cantidad
            items.append({'producto': producto, 'cantidad': cantidad, 'subtotal': subtotal})
            total += subtotal

        try:
            descuento = Decimal(str(request.POST.get('descuento', '0')))
            adicional = Decimal(str(request.POST.get('adicional', '0')))
        except (ValueError, TypeError):
            descuento = Decimal('0.00')
            adicional = Decimal('0.00')

        total_final = total - descuento + adicional

        return render(request, 'carrito.html', {
            'items': items,
            'total': total,
            'descuento': descuento,
            'adicional': adicional,
            'total_final': total_final,
        })

    return redirect('carrito')

@login_required
def buscar_producto(request):
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
            'precio': str(p.precio),
        })

    return JsonResponse(results, safe=False)
