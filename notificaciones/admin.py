from django.contrib import admin
from .models import Notificacion, DeviceToken

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    
    """Interfaz administrativa para supervisar el estado de las notificaciones."""

    list_display = ('__str__', 'estado', 'created_at')
    list_filter = ('estado',)
    autocomplete_fields = ['evento', 'destinatario']
    search_fields = ('evento__titulo', 'destinatario__username')

@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):

    """Interfaz administrativa para la gestión de tokens de dispositivos."""

    list_display = ('user', 'device_type', 'is_active', 'created_at')
    list_filter = ('device_type', 'is_active')
    search_fields = ('user__username', 'token')
    autocomplete_fields = ['user']
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
