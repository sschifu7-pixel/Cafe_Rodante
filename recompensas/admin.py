from django.contrib import admin
from .models import Cliente, Producto, Venta, DetalleVenta, Recompensa, MovimientoPuntos

# Inline para ver movimientos de puntos del cliente
class MovimientoPuntosInline(admin.TabularInline):
    model = MovimientoPuntos
    extra = 0
    readonly_fields = ('fecha',)
    fields = ('tipo', 'cantidad', 'referencia', 'recompensa', 'venta', 'estado_entrega', 'fecha')
    can_delete = False

# Inline para ver el detalle de la venta
class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    fields = ('producto', 'cantidad', 'subtotal')

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nfc_uid', 'telefono', 'crepipuntos', 'estado', 'fecha_registro')
    list_filter = ('estado', 'fecha_registro')
    search_fields = ('nombre', 'nfc_uid', 'telefono')
    readonly_fields = ('crepipuntos', 'fecha_registro')
    inlines = [MovimientoPuntosInline]
    actions = ['bloquear_llavero', 'activar_llavero']

    def bloquear_llavero(self, request, queryset):
        queryset.update(estado='bloqueado')
        self.message_user(request, "Los llaveros seleccionados han sido bloqueados.")
    bloquear_llavero.short_description = "Bloquear llaveros seleccionados"

    def activar_llavero(self, request, queryset):
        queryset.update(estado='activo')
        self.message_user(request, "Los llaveros seleccionados han sido activados.")
    activar_llavero.short_description = "Activar llaveros seleccionados"


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'puntos_que_otorga', 'stock')
    search_fields = ('nombre',)
    list_filter = ('puntos_que_otorga',)


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'empleado', 'total', 'fecha')
    list_filter = ('fecha', 'empleado')
    search_fields = ('cliente__nombre', 'empleado__username')
    inlines = [DetalleVentaInline]
    readonly_fields = ('fecha',)


@admin.register(Recompensa)
class RecompensaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'puntos_requeridos', 'activa')
    search_fields = ('nombre',)
    list_filter = ('activa',)


@admin.register(MovimientoPuntos)
class MovimientoPuntosAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'tipo', 'cantidad', 'referencia', 'fecha', 'estado_entrega')
    list_filter = ('tipo', 'fecha', 'estado_entrega')
    search_fields = ('cliente__nombre', 'referencia')
    readonly_fields = ('fecha',)

