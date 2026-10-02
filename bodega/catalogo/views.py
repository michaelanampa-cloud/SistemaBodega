from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q

from productos.models import Producto


def catalogo_view(request):
    query = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    solo_ofertas = request.GET.get('ofertas', '').strip().lower() == '1'
    productos = Producto.objects.all().order_by('-en_oferta', '-created_at')

    if solo_ofertas:
        productos = productos.filter(en_oferta=True)

    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) | Q(detalle__icontains=query)
        )

    if tipo:
        productos = productos.filter(tipoProducto__iexact=tipo)

    paginator = Paginator(productos, 18)  # Mostrar 18 productos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    tipos_disponibles = Producto.objects.values_list('tipoProducto', flat=True).distinct().order_by('tipoProducto')

    return render(request, 'catalogo.html', {
        'page_obj': page_obj,
        'query': query,
        'tipo': tipo,
        'solo_ofertas': solo_ofertas,
        'tipos_disponibles': tipos_disponibles,
    })
