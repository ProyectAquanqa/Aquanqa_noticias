from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModelWithAudit
from eventos.models import Evento


class Notificacion(BaseModelWithAudit):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('enviado', 'Enviado'),
        ('fallido', 'Fallido'),
    )
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="notificaciones")
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="notificaciones_recibidas")
    estado = models.CharField(max_length=10, choices=ESTADOS, default='pendiente', db_index=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-created_at']

    def __str__(self):
        dest = self.destinatario.username if self.destinatario else "Broadcast"
        return f"Notificación de '{self.evento.titulo}' para {dest} ({self.estado})"


class DeviceToken(BaseModelWithAudit):
    DEVICE_CHOICES = (
        ('android', 'Android'),
        ('ios', 'iOS'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="device_tokens")
    token = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(max_length=10, choices=DEVICE_CHOICES, default='android')
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Device Token"
        verbose_name_plural = "Device Tokens"
        ordering = ['-created_at']

    def __str__(self):
        return f"Token de {self.user.username} para {self.get_device_type_display()}"
