from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from productos.models import Producto

class Command(BaseCommand):

    help = 'Crea y configura los roles Administrador y Empleado'

    def handle(self, *args, **kwargs):

        User = get_user_model()

        # ==========================================
        # CREAR GRUPOS
        # ==========================================

        grupo_admin, _ = Group.objects.get_or_create(
            name='Administrador'
        )

        grupo_empleado, _ = Group.objects.get_or_create(
            name='Empleado'
        )


        # ==========================================
        # PERMISOS DE USUARIOS
        # ==========================================

        permisos_usuario = Permission.objects.filter(
            content_type__app_label='auth',
            content_type__model='user',
            codename__in=[
                'view_user',
                'add_user',
                'change_user',
            ]
        )

        grupo_admin.permissions.add(*permisos_usuario)


        # ==========================================
        # PERMISO PARA REGISTRAR PRODUCTOS
        # ==========================================

        content_type_producto = ContentType.objects.get_for_model(
            Producto
        )

        permiso_agregar_producto = Permission.objects.get(
            content_type=content_type_producto,
            codename='add_producto'
        )

        grupo_admin.permissions.add(
            permiso_agregar_producto
        )


        # ==========================================
        # EMPLEADO: VER PRODUCTOS
        # ==========================================

        permisos_producto_empleado = Permission.objects.filter(
            content_type=content_type_producto,
            codename='view_producto'
        )

        grupo_empleado.permissions.add(
            *permisos_producto_empleado
        )


        self.stdout.write(
            self.style.SUCCESS(
                'Roles configurados correctamente.'
            )
        )

        self.stdout.write(
            'Administrador: administrar usuarios y registrar productos.'
        )

        self.stdout.write(
            'Empleado: puede consultar productos.'
        )

