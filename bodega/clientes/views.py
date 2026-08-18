from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from .models import Cliente
from .forms import ClienteForm

import requests
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse

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

def consultar_dni(request):
    if request.method != 'GET':
        return JsonResponse({
            'success': False,
            'mensaje': 'Método no permitido.'
        }, status=405)

    dni = request.GET.get('dni', '').strip()

    if not dni.isdigit() or len(dni) != 8:
        return JsonResponse({
            'success': False,
            'mensaje': 'El DNI debe contener exactamente 8 dígitos.'
        }, status=400)

    cliente = Cliente.objects.filter(dni=dni).first()

    if cliente:
        return JsonResponse({
            'success': True,
            'encontrado_bd': True,
            'cliente_registrado': True,
            'datos': {
                'dni': cliente.dni,
                'nombre': cliente.nombre,
                'email': cliente.email,
                'telefono': cliente.telefono,
                'direccion': cliente.direccion,
            }
        })

    token = getattr(settings, 'API_DNI_TOKEN', '')

    if not token:
        return JsonResponse({
            'success': False,
            'mensaje': 'No se ha configurado el token de consulta DNI.'
        }, status=500)

    try:
        respuesta = requests.post(
            'https://api.apiperu.dev/dni',
            json={
                'dni': dni
            },
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
            },
            timeout=10
        )

        datos = respuesta.json()

        print("RESPUESTA API DNI:")
        print(datos)

        if respuesta.status_code != 200:
            return JsonResponse({
                'success': False,
                'mensaje': datos.get(
                    'message',
                    'No se encontró información para este DNI.'
                )
            }, status=404)

        return JsonResponse({
            'success': True,
            'datos': datos
        })

    except requests.exceptions.Timeout:
        return JsonResponse({
            'success': False,
            'mensaje': 'La consulta tardó demasiado.'
        }, status=504)

    except requests.exceptions.RequestException as e:
        print("ERROR API DNI:", e)

        return JsonResponse({
            'success': False,
            'mensaje': 'No fue posible conectar con el servicio DNI.'
        }, status=503)

    except ValueError:
        return JsonResponse({
            'success': False,
            'mensaje': 'La respuesta del servicio no es válida.'
        }, status=502)