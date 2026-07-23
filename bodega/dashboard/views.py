from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render

from carrito.models import Compra
from clientes.models import Cliente
from gastos.models import Gasto, Proveedor


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


@login_required
def dashboard_view(request):
    start_date = _parse_date(request.GET.get('start_date'))
    end_date = _parse_date(request.GET.get('end_date'))
    tipo = request.GET.get('tipo', '').strip()

    compras = Compra.objects.order_by('-fecha')
    gastos = Gasto.objects.order_by('-fecha')

    if start_date:
        compras = compras.filter(fecha__date__gte=start_date)
        gastos = gastos.filter(fecha__date__gte=start_date)
    if end_date:
        compras = compras.filter(fecha__date__lte=end_date)
        gastos = gastos.filter(fecha__date__lte=end_date)
    if tipo:
        compras = compras.filter(tipo_compra=tipo)
        gastos = gastos.filter(tipo_compra=tipo)

    total_compras = compras.aggregate(total=Sum('total'))['total'] or 0
    total_gastos = gastos.aggregate(total=Sum('total'))['total'] or 0
    balance = total_compras - total_gastos

    chart_data = [
        {'label': 'Compras', 'total': float(total_compras or 0)},
        {'label': 'Gastos', 'total': float(total_gastos or 0)},
    ]

    return render(request, 'dashboard.html', {
        'compras': compras[:10],
        'gastos': gastos[:10],
        'total_compras': total_compras,
        'total_gastos': total_gastos,
        'balance': balance,
        'chart_data': chart_data,
        'start_date': start_date,
        'end_date': end_date,
        'tipo': tipo,
    })


@login_required
def resumen_gastos(request):
    start_date = _parse_date(request.GET.get('start_date'))
    end_date = _parse_date(request.GET.get('end_date'))
    proveedor_id = request.GET.get('proveedor', '').strip()

    gastos = Gasto.objects.order_by('-fecha')

    if start_date:
        gastos = gastos.filter(fecha__date__gte=start_date)
    if end_date:
        gastos = gastos.filter(fecha__date__lte=end_date)
    if proveedor_id:
        gastos = gastos.filter(proveedor_id=proveedor_id)

    total_gastos = gastos.aggregate(total=Sum('total'))['total'] or 0
    resumen_por_tipo = list(gastos.values('tipo_compra').annotate(cantidad=Count('id'), total=Sum('total')).order_by('-total'))
    proveedores = Proveedor.objects.filter(activo=True)

    return render(request, 'resumen_gastos.html', {
        'gastos': gastos[:10],
        'total_gastos': total_gastos,
        'resumen_por_tipo': resumen_por_tipo,
        'proveedores': proveedores,
        'start_date': start_date,
        'end_date': end_date,
        'proveedor_id': proveedor_id,
    })

def resumen_gastos1(request):
    gastos = Gasto.objects.order_by('-fecha')
    total_gastos = gastos.aggregate(total=Sum('total'))['total'] or 0
    resumen_por_tipo = list(gastos.values('tipo_compra').annotate(cantidad=Count('id'), total=Sum('total')).order_by('-total'))
    return render(request, 'resumen_gastos.html', {
        'gastos': gastos,
        'total_gastos': total_gastos,
        'resumen_por_tipo': resumen_por_tipo,
    })


@login_required
def resumen_compras(request):
    start_date = _parse_date(request.GET.get('start_date'))
    end_date = _parse_date(request.GET.get('end_date'))
    cliente_id = request.GET.get('cliente', '').strip()

    compras = Compra.objects.order_by('-fecha')

    if start_date:
        compras = compras.filter(fecha__date__gte=start_date)
    if end_date:
        compras = compras.filter(fecha__date__lte=end_date)
    if cliente_id:
        compras = compras.filter(cliente_id=cliente_id)

    total_compras = compras.aggregate(total=Sum('total'))['total'] or 0
    resumen_por_tipo = list(compras.values('tipo_compra').annotate(cantidad=Count('id'), total=Sum('total')).order_by('-total'))
    clientes = Cliente.objects.filter(activo=True)

    return render(request, 'resumen_compras.html', {
        'compras': compras[:10],
        'total_compras': total_compras,
        'resumen_por_tipo': resumen_por_tipo,
        'clientes': clientes,
        'start_date': start_date,
        'end_date': end_date,
        'cliente_id': cliente_id,
    })
