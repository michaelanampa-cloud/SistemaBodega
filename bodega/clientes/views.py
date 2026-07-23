from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from .models import Cliente
from .forms import ClienteForm


@require_http_methods(["GET", "POST"])
def registro_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm()
    return render(request, 'clientes/registroClientes.html', {'form': form})


def lista_clientes(request):
    clientes = Cliente.objects.filter(activo=True)
    return render(request, 'clientes/listaClientes.html', {'clientes': clientes})


def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'clientes/registroClientes.html', {'form': form, 'cliente': cliente})


def eliminar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.activo = False
        cliente.save()
        return redirect('lista_clientes')
    return render(request, 'clientes/confirmar_eliminar.html', {'cliente': cliente})
