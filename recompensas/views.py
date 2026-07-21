from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ValidationError
import json
from decimal import Decimal

from django.contrib.auth import logout as auth_logout

from .models import Cliente, Producto, Venta, DetalleVenta, Recompensa, MovimientoPuntos


def logout_view(request):
    """Cerrar sesión de forma segura y redirigir a la pantalla de login."""
    auth_logout(request)
    return redirect('login')


def _inicializar_datos_demo():
    """Poblar datos iniciales de demostración en caso de que la base de datos esté vacía."""
    from .apps import crear_datos_iniciales
    crear_datos_iniciales(None)




@login_required
def home(request):
    _inicializar_datos_demo()
    return render(request, 'recompensas/home.html')



@login_required
def scanner(request):
    return render(request, 'recompensas/home.html')



@login_required
def buscar_cliente(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'status': 'error', 'message': 'Consulta vacía'}, status=400)

    clientes = Cliente.objects.filter(
        Q(nfc_uid__iexact=query) |
        Q(nombre__icontains=query) |
        Q(telefono__contains=query)
    )

    results = [
        {
            'nombre': c.nombre,
            'nfc_uid': c.nfc_uid,
            'telefono': c.telefono or '',
            'crepipuntos': c.crepipuntos,
            'estado': c.estado,
            'url': f"/cliente/{c.nfc_uid}/"
        }
        for c in clientes
    ]

    return JsonResponse({'status': 'success', 'results': results})


@login_required
def registrar_cliente(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        nfc_uid = request.POST.get('nfc_uid', '').strip().upper()
        telefono = request.POST.get('telefono', '').strip()
        cumpleanos = request.POST.get('cumpleanos', '')
        
        if not nombre or not nfc_uid:
            messages.error(request, "El nombre y el UID del NFC son obligatorios.")
            return render(request, 'recompensas/registrar_nfc.html')
            
        if Cliente.objects.filter(nfc_uid=nfc_uid).exists():
            messages.error(request, f"Ya existe un llavero registrado con el UID '{nfc_uid}'.")
            return render(request, 'recompensas/registrar_nfc.html', {'nombre': nombre, 'telefono': telefono, 'cumpleanos': cumpleanos})
            
        try:
            with transaction.atomic():
                cliente = Cliente.objects.create(
                    nombre=nombre,
                    nfc_uid=nfc_uid,
                    telefono=telefono or None,
                    cumpleanos=cumpleanos or None,
                    estado='activo'
                )
                
                # Crear movimiento de bienvenida de 2 puntos
                MovimientoPuntos.objects.create(
                    cliente=cliente,
                    tipo='acumulacion',
                    cantidad=2,
                    referencia='Regalo de bienvenida'
                )
                
            messages.success(request, f"Llavero activado con éxito para {cliente.nombre}. ¡Se han otorgado +2 puntos de bienvenida!")
            return redirect('cliente_dashboard', nfc_uid=cliente.nfc_uid)
            
        except Exception as e:
            messages.error(request, f"Ocurrió un error al registrar: {str(e)}")
            return render(request, 'recompensas/registrar_nfc.html', {'nombre': nombre, 'nfc_uid': nfc_uid, 'telefono': telefono, 'cumpleanos': cumpleanos})
            
    return render(request, 'recompensas/registrar_nfc.html')


@login_required
def cliente_dashboard(request, nfc_uid):
    cliente = get_object_or_404(Cliente, nfc_uid__iexact=nfc_uid)
    
    if cliente.estado == 'bloqueado':
        return render(request, 'recompensas/cliente_bloqueado.html', {'cliente': cliente})
        
    productos = Producto.objects.filter(stock__gt=0)
    
    # Calcular puntos para la siguiente recompensa (basado en catálogo, ej: 20 puntos)
    siguiente_recompensa = Recompensa.objects.filter(activa=True).order_by('puntos_requeridos').first()
    puntos_requeridos = siguiente_recompensa.puntos_requeridos if siguiente_recompensa else 20
    
    faltan_puntos = 0
    porcentaje = 100
    if cliente.crepipuntos < puntos_requeridos:
        faltan_puntos = puntos_requeridos - cliente.crepipuntos
        porcentaje = int((cliente.crepipuntos / puntos_requeridos) * 100)
        
    context = {
        'cliente': cliente,
        'productos': productos,
        'siguiente_recompensa': siguiente_recompensa,
        'puntos_requeridos': puntos_requeridos,
        'faltan_puntos': faltan_puntos,
        'porcentaje': porcentaje,
        'active_tab': 'inicio'
    }
    return render(request, 'recompensas/cliente_dashboard.html', context)


@login_required
def cliente_historial(request, nfc_uid):
    cliente = get_object_or_404(Cliente, nfc_uid__iexact=nfc_uid)
    movimientos = cliente.movimientos_puntos.all().order_by('-fecha')
    
    context = {
        'cliente': cliente,
        'movimientos': movimientos,
        'active_tab': 'historial'
    }
    return render(request, 'recompensas/historial.html', context)


@login_required
def cliente_canjear(request, nfc_uid):
    cliente = get_object_or_404(Cliente, nfc_uid__iexact=nfc_uid)
    recompensas = Recompensa.objects.filter(activa=True).order_by('puntos_requeridos')
    
    context = {
        'cliente': cliente,
        'recompensas': recompensas,
        'active_tab': 'canjear'
    }
    return render(request, 'recompensas/canjear.html', context)


@login_required
@require_POST
def registrar_compra(request, nfc_uid):
    cliente = get_object_or_404(Cliente, nfc_uid__iexact=nfc_uid)
    
    if cliente.estado == 'bloqueado':
        return JsonResponse({'status': 'error', 'message': 'El llavero de este cliente está bloqueado.'}, status=403)
        
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        
        if not items:
            return JsonResponse({'status': 'error', 'message': 'No se seleccionaron productos.'}, status=400)
            
        total_venta = Decimal("0.00")
        total_puntos = 0
        detalles_a_crear = []
        productos_a_actualizar = []
        
        with transaction.atomic():
            venta = Venta.objects.create(
                cliente=cliente,
                empleado=request.user,
                total=total_venta # Se actualizará al final
            )
            
            for item in items:
                prod_id = item.get('id')
                cantidad = int(item.get('cantidad', 0))
                
                if cantidad <= 0:
                    continue
                    
                producto = Producto.objects.select_for_update().get(id=prod_id)
                
                if producto.stock < cantidad:
                    raise ValidationError(f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}")
                    
                subtotal = producto.precio * cantidad
                total_venta += subtotal
                
                # Cada producto otorga sus puntos definidos
                puntos_producto = producto.puntos_que_otorga * cantidad
                total_puntos += puntos_producto
                
                # Restar stock
                producto.stock -= cantidad
                productos_a_actualizar.append(producto)
                
                detalles_a_crear.append(DetalleVenta(
                    venta=venta,
                    producto=producto,
                    cantidad=cantidad,
                    subtotal=subtotal
                ))
            
            if not detalles_a_crear:
                raise ValidationError("No hay detalles válidos para registrar.")
                
            # Guardar detalles y actualizar productos
            DetalleVenta.objects.bulk_create(detalles_a_crear)
            for p in productos_a_actualizar:
                p.save()
                
            # Actualizar total de la venta
            venta.total = total_venta
            venta.save()
            
            # Registrar el movimiento de puntos (+puntos)
            referencia_compra = f"Compra registrada - Venta #{venta.id}"
            MovimientoPuntos.objects.create(
                cliente=cliente,
                tipo='acumulacion',
                cantidad=total_puntos,
                referencia=referencia_compra,
                venta=venta
            )
            
        return JsonResponse({
            'status': 'success',
            'message': 'Compra registrada exitosamente.',
            'puntos_ganados': total_puntos,
            'nuevo_saldo': cliente.crepipuntos,
            'venta_id': venta.id
        })
        
    except Producto.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Uno de los productos seleccionados no existe.'}, status=404)
    except ValidationError as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error interno: {str(e)}'}, status=500)


@login_required
@require_POST
def realizar_canje(request, nfc_uid):
    cliente = get_object_or_404(Cliente, nfc_uid__iexact=nfc_uid)
    
    if cliente.estado == 'bloqueado':
        return JsonResponse({'status': 'error', 'message': 'El llavero de este cliente está bloqueado.'}, status=403)
        
    try:
        data = json.loads(request.body)
        recompensa_id = data.get('recompensa_id')
        
        recompensa = get_object_or_404(Recompensa, id=recompensa_id, activa=True)
        
        if cliente.crepipuntos < recompensa.puntos_requeridos:
            return JsonResponse({
                'status': 'error',
                'message': f'Puntos insuficientes. Requiere {recompensa.puntos_requeridos} y tiene {cliente.crepipuntos}.'
            }, status=400)
            
        with transaction.atomic():
            # Crear movimiento de puntos negativo
            MovimientoPuntos.objects.create(
                cliente=cliente,
                tipo='canje',
                cantidad=-recompensa.puntos_requeridos,
                referencia=f"Recompensa utilizada - {recompensa.nombre}",
                recompensa=recompensa,
                estado_entrega='entregado'
            )
            
        return JsonResponse({
            'status': 'success',
            'message': f'¡Canje realizado con éxito! Se ha entregado: {recompensa.nombre}.',
            'puntos_restados': recompensa.puntos_requeridos,
            'nuevo_saldo': cliente.crepipuntos
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error interno: {str(e)}'}, status=500)


@login_required
def cliente_perfil(request, nfc_uid):
    cliente = get_object_or_404(Cliente, nfc_uid__iexact=nfc_uid)
    
    # Calcular estadísticas básicas para mostrar en el perfil
    total_compras = cliente.ventas.count()
    total_canjes = cliente.movimientos_puntos.filter(tipo='canje').count()
    
    context = {
        'cliente': cliente,
        'total_compras': total_compras,
        'total_canjes': total_canjes,
        'active_tab': 'perfil'
    }
    return render(request, 'recompensas/perfil.html', context)


