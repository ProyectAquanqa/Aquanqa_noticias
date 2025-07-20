from django.contrib import admin
from .models import Notificacion, DeviceToken

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('evento', 'destinatario', 'estado', 'created_at')
    list_filter = ('estado',)
    autocomplete_fields = ['evento', 'destinatario']
    search_fields = ('evento__titulo', 'destinatario__username')

@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'is_active', 'created_at')
    list_filter = ('device_type', 'is_active')
    search_fields = ('user__username',)
    autocomplete_fields = ['user']
