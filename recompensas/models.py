from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Cliente(models.Model):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('bloqueado', 'Bloqueado'),
    ]
    
    nombre = models.CharField(max_length=100, verbose_name="Nombre o Apodo")
    nfc_uid = models.CharField(max_length=50, unique=True, db_index=True, verbose_name="UID de Llavero NFC")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    cumpleanos = models.DateField(blank=True, null=True, verbose_name="Fecha de Cumpleaños")
    crepipuntos = models.IntegerField(default=0, verbose_name="Crepipuntos Acumulados")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo', verbose_name="Estado del Llavero")
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return f"{self.nombre} ({self.nfc_uid}) - {self.crepipuntos} pts"


class Producto(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Producto")
    precio = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Precio ($)")
    puntos_que_otorga = models.IntegerField(default=2, verbose_name="Crepipuntos que otorga")
    stock = models.IntegerField(default=100, verbose_name="Stock disponible")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return f"{self.nombre} - ${self.precio} (+{self.puntos_que_otorga} pts)"


class Venta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='ventas', verbose_name="Cliente")
    empleado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='ventas_registradas', verbose_name="Empleado")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora")
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Total Pagado ($)")

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"

    def __str__(self):
        cliente_nombre = self.cliente.nombre if self.cliente else "General"
        return f"Venta #{self.id} - {cliente_nombre} - ${self.total} ({self.fecha.strftime('%d/%m/%Y %H:%M')})"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles', verbose_name="Venta")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='detalles_venta', verbose_name="Producto")
    cantidad = models.PositiveIntegerField(default=1, verbose_name="Cantidad")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Subtotal ($)")

    class Meta:
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalles de Ventas"

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre} en Venta #{self.venta.id}"


class Recompensa(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la Recompensa")
    puntos_requeridos = models.IntegerField(default=20, verbose_name="Crepipuntos Requeridos")
    activa = models.BooleanField(default=True, verbose_name="Activa / Disponible")

    class Meta:
        verbose_name = "Recompensa"
        verbose_name_plural = "Recompensas"

    def __str__(self):
        return f"{self.nombre} ({self.puntos_requeridos} pts)"


class MovimientoPuntos(models.Model):
    TIPO_CHOICES = [
        ('acumulacion', 'Acumulación'),
        ('canje', 'Canje'),
        ('ajuste', 'Ajuste'),
    ]
    ESTADO_ENTREGA_CHOICES = [
        ('entregado', 'Entregado'),
        ('pendiente', 'Pendiente'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='movimientos_puntos', verbose_name="Cliente")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo de Movimiento")
    cantidad = models.IntegerField(verbose_name="Puntos") # Positivo para acumulación, negativo para canjes
    referencia = models.CharField(max_length=200, blank=True, null=True, verbose_name="Referencia")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    recompensa = models.ForeignKey(Recompensa, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Recompensa asociada")
    venta = models.ForeignKey(Venta, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Venta asociada")
    estado_entrega = models.CharField(max_length=20, choices=ESTADO_ENTREGA_CHOICES, default='entregado', verbose_name="Estado de Entrega")

    class Meta:
        verbose_name = "Movimiento de Puntos"
        verbose_name_plural = "Movimientos de Puntos"

    def __str__(self):
        signo = "+" if self.cantidad >= 0 else ""
        return f"{self.cliente.nombre}: {signo}{self.cantidad} pts ({self.get_tipo_display()}) - {self.fecha.strftime('%d/%m/%Y %H:%M')}"

    def clean(self):
        # Validar si un cliente tiene suficientes puntos para un canje
        if self.tipo == 'canje' and self.cantidad < 0:
            puntos_necesarios = abs(self.cantidad)
            # Para evitar problemas con el propio objeto actualizándose, restamos la cantidad vieja si es edición
            puntos_disponibles = self.cliente.crepipuntos
            if self.pk:
                puntos_disponibles -= MovimientoPuntos.objects.get(pk=self.pk).cantidad
            
            if puntos_disponibles < puntos_necesarios:
                raise ValidationError(f"El cliente no tiene suficientes crepipuntos. Tiene {puntos_disponibles} y requiere {puntos_necesarios}.")

    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = self.pk is None
        old_cantidad = 0
        if not is_new:
            old_instance = MovimientoPuntos.objects.get(pk=self.pk)
            old_cantidad = old_instance.cantidad

        super().save(*args, **kwargs)

        # Sincronizar saldo de crepipuntos del cliente
        cliente = self.cliente
        if is_new:
            cliente.crepipuntos += self.cantidad
        else:
            cliente.crepipuntos = cliente.crepipuntos - old_cantidad + self.cantidad
        cliente.save()

    def delete(self, *args, **kwargs):
        cliente = self.cliente
        # Revertir el saldo al eliminar el movimiento
        cliente.crepipuntos -= self.cantidad
        cliente.save()
        super().delete(*args, **kwargs)

