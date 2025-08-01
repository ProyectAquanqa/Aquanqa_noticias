from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Evento
from notificaciones.models import Notificacion
from notificaciones.services import send_push_notification

@receiver(post_save, sender=Evento)
def crear_y_enviar_notificacion_al_publicar(sender, instance, created, update_fields, **kwargs):
    """
    Señal que se dispara al guardar un Evento.

    Si el evento se marca como 'publicado' (ya sea al crearse o al actualizarse),
    crea un registro de Notificacion y desencadena el envío de notificaciones push.
    """
    # Determinar si el campo 'publicado' fue explícitamente parte de la actualización.
    # Si `update_fields` es None, se asume que cualquier campo pudo haber cambiado.
    publicado_field_updated = update_fields is None or 'publicado' in update_fields

    # La condición se cumple si el evento está publicado Y es una creación nueva o se está actualizando el campo 'publicado'.
    if instance.publicado and (created or publicado_field_updated):
        # Evitar enviar notificaciones duplicadas para el mismo evento.
        if not Notificacion.objects.filter(evento=instance, leido=True).exists():
            trigger_notification(instance)

def trigger_notification(evento):
    """Crea el objeto Notificacion y llama al servicio de envío."""
    # El usuario que actualizó por última vez el evento es el responsable.
    audit_user = evento.updated_by
    notificacion = Notificacion.objects.create(
        evento=evento,
        created_by=audit_user,
        updated_by=audit_user
    )
    
    # TODO: ¡Crítico en producción! Esta llamada debe ser asíncrona.
    # Usar Celery u otro sistema de colas para no bloquear la petición HTTP.
    # Ejemplo: send_push_notification.delay(notificacion.id)
    send_push_notification(notificacion.id)