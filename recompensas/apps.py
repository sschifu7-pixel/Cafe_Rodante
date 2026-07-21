from django.apps import AppConfig
from django.db.models.signals import post_migrate


def crear_datos_iniciales(sender, **kwargs):
    from django.contrib.auth.models import User

    try:
        if User.objects.filter(username='admin').count() == 0:
            User.objects.create_superuser('admin', 'admin@caferodante.com', 'admin123', first_name='Administrador')

        if User.objects.filter(username='empleado').count() == 0:
            User.objects.create_user('empleado', 'empleado@caferodante.com', 'empleado123', first_name='Empleado')
    except Exception:
        pass



class RecompensasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recompensas'

    def ready(self):
        post_migrate.connect(crear_datos_iniciales, sender=self)

