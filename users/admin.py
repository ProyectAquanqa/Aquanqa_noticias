from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario
from core.admin import AuditModelAdmin

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin, AuditModelAdmin):
    # Los fieldsets de UserAdmin ya son bastante completos.
    # Podemos añadir nuestros campos personalizados.
    
    # Añadir los campos personalizados a los fieldsets existentes
    # (name, permissions, date info)
    fieldsets = UserAdmin.fieldsets + (
        ('Campos Personalizados', {'fields': ('foto_perfil', 'firma')}),
    )
    
    # Si quieres mostrar los campos en la lista de usuarios
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
