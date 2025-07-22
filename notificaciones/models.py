from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModelWithAudit
from eventos.models import Evento


class Notificacion(BaseModelWithAudit):
    """
    Registra una notificación enviada o por enviar.
    
    Actúa como un historial de las comunicaciones push. Si `destinatario` es
    nulo, se considera una notificación de tipo 'broadcast' (para todos).
    """
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('enviado', 'Enviado'),
        ('fallido', 'Fallido'),
    )
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="notificaciones")
    destinatario = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, 
        related_name="notificaciones_recibidas",
        help_text="Usuario específico a notificar. Nulo para notificaciones broadcast."
    )
    estado = models.CharField(max_length=10, choices=ESTADOS, default='pendiente', db_index=True)
    error_message = models.TextField(blank=True, null=True, help_text="Mensaje de error si el envío falla.")

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-created_at']

    def __str__(self):
        dest = self.destinatario.username if self.destinatario else "Broadcast"
        return f"Notificación de '{self.evento.titulo}' para {dest} ({self.estado})"


class DeviceToken(BaseModelWithAudit):
    """
    Almacena un token de un dispositivo móvil (FCM) para notificaciones push.
    
    Cada token está asociado a un usuario y un tipo de dispositivo (iOS/Android).
    """
    DEVICE_CHOICES = (
        ('android', 'Android'),
        ('ios', 'iOS'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="device_tokens")
    token = models.CharField(max_length=255, unique=True, help_text="Token de registro de Firebase Cloud Messaging.")
    device_type = models.CharField(max_length=10, choices=DEVICE_CHOICES, default='android')
    is_active = models.BooleanField(default=True, db_index=True, help_text="Indica si el token es válido para recibir notificaciones.")

    class Meta:
        verbose_name = "Token de Dispositivo"
        verbose_name_plural = "Tokens de Dispositivos"
        ordering = ['-created_at']

    def __str__(self):
        return f"Token de {self.user.username} ({self.get_device_type_display()})"
