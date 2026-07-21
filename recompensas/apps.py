from django.apps import AppConfig
from django.db.models.signals import post_migrate


def crear_datos_iniciales(sender, **kwargs):
    from django.contrib.auth.models import User
    from decimal import Decimal
    from .models import Cliente, Producto, Recompensa, MovimientoPuntos

    try:
        if User.objects.filter(is_superuser=True).count() == 0:
            User.objects.create_superuser('admin', 'admin@caferodante.com', 'admin123', first_name='Empleado')

        if Producto.objects.count() == 0:
            Producto.objects.create(nombre="Crepa Clásica", precio=Decimal("45.00"), puntos_que_otorga=2, stock=150)
            Producto.objects.create(nombre="Frappé Oreo", precio=Decimal("55.00"), puntos_que_otorga=2, stock=120)
            Producto.objects.create(nombre="Espresso Americano", precio=Decimal("30.00"), puntos_que_otorga=2, stock=200)
            Producto.objects.create(nombre="Capuccino Vainilla", precio=Decimal("45.00"), puntos_que_otorga=2, stock=180)
            Producto.objects.create(nombre="Crepa Nutella Plátano", precio=Decimal("55.00"), puntos_que_otorga=2, stock=100)

        if Recompensa.objects.count() == 0:
            Recompensa.objects.create(nombre="Producto gratis (Crepa o Bebida)", puntos_requeridos=20, activa=True)
            Recompensa.objects.create(nombre="Playera Edición Café Rodante", puntos_requeridos=60, activa=True)
            Recompensa.objects.create(nombre="Termo Metálico Café Rodante", puntos_requeridos=100, activa=True)

        if Cliente.objects.count() == 0:
            dante = Cliente.objects.create(
                nombre="Dante",
                nfc_uid="CRP-7A3F6B",
                telefono="5512345678",
                cumpleanos="1995-06-12",
                estado="activo"
            )
            MovimientoPuntos.objects.create(cliente=dante, tipo="acumulacion", cantidad=2, referencia="Regalo de bienvenida")
            MovimientoPuntos.objects.create(cliente=dante, tipo="acumulacion", cantidad=6, referencia="Compra registrada - Venta de prueba 1")
            MovimientoPuntos.objects.create(cliente=dante, tipo="acumulacion", cantidad=14, referencia="Compra registrada - Venta de prueba 2")
            MovimientoPuntos.objects.create(
                cliente=dante,
                tipo="canje",
                cantidad=-20,
                referencia="Recompensa utilizada - Producto gratis",
                recompensa=Recompensa.objects.first()
            )
            MovimientoPuntos.objects.create(cliente=dante, tipo="acumulacion", cantidad=16, referencia="Compra registrada - Venta de prueba 3")
    except Exception:
        pass


class RecompensasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recompensas'

    def ready(self):
        post_migrate.connect(crear_datos_iniciales, sender=self)

