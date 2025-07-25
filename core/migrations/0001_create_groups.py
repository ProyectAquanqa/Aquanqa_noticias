# Generated by Django 5.2.4 on 2025-07-15 17:17

from django.db import migrations
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

# ==============================================================================
# CONFIGURACIÓN DE ROLES Y PERMISOS
# ==============================================================================
# Este diccionario es la "única fuente de verdad" para la configuración de roles.
# Es declarativo y fácil de leer.
#
# Formato:
#   "Nombre del Rol": {
#       "access_all": ["<app_label1>", "<app_label2>"],  # Da TODOS los permisos (CRUDV) sobre todas las tablas de estas apps.
#       "view_only": ["<app_label3>", "<app_label4>"],   # Da SÓLO permisos de LECTURA (view) sobre todas las tablas de estas apps.
#   }
#
ROLES_CONFIG = {
    "Admin": {
        "description": "Control total sobre los módulos principales de la aplicación.",
        "access_all": ["eventos", "chatbot", "core"],
    },
    "QA": {
        "description": "Gestión completa del contenido de eventos (Crear, Editar, Borrar).",
        "access_all": ["eventos"],
    },
    "Trabajador": {
        "description": "Acceso de solo lectura a toda la información para consulta.",
        "view_only": ["eventos", "chatbot"],
    }
}
# ==============================================================================

def create_groups_from_config(apps, schema_editor):
    """
    Lee la configuración de ROLES_CONFIG y la aplica a la base de datos.
    """
    for role_name, config in ROLES_CONFIG.items():
        group, created = Group.objects.get_or_create(name=role_name)
        if created:
            print(f"Grupo '{role_name}' creado. {config.get('description', '')}")

        # Limpiamos permisos para asegurar una asignación limpia cada vez
        group.permissions.clear()

        # Asignar permisos de acceso total (CRUDV)
        if "access_all" in config:
            app_labels = config["access_all"]
            content_types = ContentType.objects.filter(app_label__in=app_labels)
            permissions = Permission.objects.filter(content_type__in=content_types)
            group.permissions.add(*permissions)

        # Asignar permisos de solo lectura (View)
        if "view_only" in config:
            app_labels = config["view_only"]
            content_types = ContentType.objects.filter(app_label__in=app_labels)
            permissions = Permission.objects.filter(
                content_type__in=content_types,
                codename__startswith='view_'
            )
            group.permissions.add(*permissions)
        
        print(f"Permisos actualizados para el grupo '{role_name}'.")

    print("\nMigración de roles y permisos completada con éxito.")


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0001_initial'),
        ('chatbot', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_groups_from_config),
    ]
