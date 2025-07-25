from django.contrib import admin
from .models import DeviceToken, Notificacion
from core.admin import AuditModelAdmin
from core.viewsets import AuditModelViewSet

@admin.register(DeviceToken)
class DeviceTokenAdmin(AuditModelAdmin):
    list_display = ('user', 'device_type', 'is_active', 'created_at')
    list_filter = ('device_type', 'is_active')
    search_fields = ('user__username', 'token')
    autocomplete_fields = ['user']

@admin.register(Notificacion)
class NotificacionAdmin(AuditModelAdmin):
    list_display = ('destinatario', 'titulo', 'leido', 'created_at')
    list_filter = ('leido',)
    search_fields = ('titulo', 'mensaje', 'destinatario__username')
    autocomplete_fields = ['destinatario', 'evento']
