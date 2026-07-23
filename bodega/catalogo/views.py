from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q

from productos.models import Producto


def catalogo_view(request):
    query = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    productos = Producto.objects.all().order_by('-created_at')

    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) | Q(detalle__icontains=query)
        )

    if tipo:
        productos = productos.filter(tipoProducto__iexact=tipo)

    paginator = Paginator(productos, 12)  # Mostrar 12 productos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    tipos_disponibles = Producto.objects.values_list('tipoProducto', flat=True).distinct().order_by('tipoProducto')

    return render(request, 'catalogo.html', {
        'page_obj': page_obj,
        'query': query,
        'tipo': tipo,
        'tipos_disponibles': tipos_disponibles,
    })
