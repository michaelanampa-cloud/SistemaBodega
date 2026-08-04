from datetime import datetime, date
import calendar

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render

from carrito.models import Compra
from clientes.models import Cliente
from gastos.models import Gasto, Proveedor, Producto


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
    total_clientes = Cliente.objects.count()
    total_proveedores = Proveedor.objects.count()
    total_productos = Producto.objects.count()  # Assuming you have a Producto model
    total_productos_vencidos = Producto.objects.filter(fechaVencimiento__lt=datetime.now()).count()

    balance = total_compras - total_gastos

    chart_data = [
        {'label': 'Compras', 'total': float(total_compras or 0)},
        {'label': 'Gastos', 'total': float(total_gastos or 0)},
    ]

    # Preparar etiquetas de meses para el gráfico mensual
    def first_day_of_month(d):
        return date(d.year, d.month, 1)

    def next_month(d):
        if d.month == 12:
            return date(d.year + 1, 1, 1)
        return date(d.year, d.month + 1, 1)

    if start_date and end_date:
        inicio_mes = first_day_of_month(start_date)
        fin_mes = first_day_of_month(end_date)
    else:
        ahora = datetime.now().date()
        fin_mes = first_day_of_month(ahora)
        inicio_mes = first_day_of_month(date(fin_mes.year, fin_mes.month, 1))
        for _ in range(5):
            inicio_mes = first_day_of_month(date(inicio_mes.year, inicio_mes.month - 1, 1)) if inicio_mes.month > 1 else date(inicio_mes.year - 1, 12, 1)

    meses = []
    mes_actual = inicio_mes
    while mes_actual <= fin_mes:
        meses.append(mes_actual)
        mes_actual = next_month(mes_actual)

    compras_por_mes = compras.annotate(mes=TruncMonth('fecha')).values('mes').annotate(total=Sum('total')).order_by('mes')
    gastos_por_mes = gastos.annotate(mes=TruncMonth('fecha')).values('mes').annotate(total=Sum('total')).order_by('mes')

    compras_por_mes_map = {first_day_of_month(item['mes'].date() if hasattr(item['mes'], 'date') else item['mes']): float(item['total'] or 0) for item in compras_por_mes}
    gastos_por_mes_map = {first_day_of_month(item['mes'].date() if hasattr(item['mes'], 'date') else item['mes']): float(item['total'] or 0) for item in gastos_por_mes}

    monthly_chart_data = {
        'labels': [calendar.month_name[m.month] + ' ' + str(m.year) for m in meses],
        'compras': [compras_por_mes_map.get(m, 0) for m in meses],
        'gastos': [gastos_por_mes_map.get(m, 0) for m in meses],
    }

    return render(request, 'dashboard.html', {
        'compras': compras[:10],
        'gastos': gastos[:10],
        'total_compras': total_compras,
        'total_gastos': total_gastos,
        'total_clientes': total_clientes,
        'total_proveedores': total_proveedores,
        'total_productos': total_productos,
        'total_productos_vencidos': total_productos_vencidos,
        'balance': balance,
        'chart_data': chart_data,
        'monthly_chart_data': monthly_chart_data,
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

