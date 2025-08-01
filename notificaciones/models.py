from django.db import models
from django.conf import settings
from core.models import BaseModelWithAudit


class DeviceToken(BaseModelWithAudit):
    """
    Almacena un token de un dispositivo móvil (FCM) para notificaciones push.
    
    Cada token está asociado a un usuario y un tipo de dispositivo (iOS/Android).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='device_tokens'
    )
    token = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(
        max_length=10,
        choices=[('android', 'Android'), ('ios', 'iOS')],
        default='android'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Token de Dispositivo"
        verbose_name_plural = "Tokens de Dispositivos"
        unique_together = ('user', 'token')
        ordering = ['-created_at']

    def __str__(self):
        return f"Token para {self.user.username} en {self.device_type}"


class Notificacion(BaseModelWithAudit):
    """
    Registra una notificación enviada o por enviar.
    
    Actúa como un historial de las comunicaciones push. Si `destinatario` es
    nulo, se considera una notificación de tipo 'broadcast' (para todos).
    """
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        null=True,
        blank=True
    )
    titulo = models.CharField(max_length=255, default='') # Añadido default
    mensaje = models.TextField(default='') # Añadido default para la migración
    leido = models.BooleanField(default=False)
    datos = models.JSONField(null=True, blank=True)
    evento = models.ForeignKey(
        'eventos.Evento',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-created_at']

    def __str__(self):
        if self.destinatario:
            return f"Notificación para {self.destinatario.username}: {self.titulo}"
        return f"Notificación broadcast: {self.titulo}"