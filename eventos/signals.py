from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Evento
from notificaciones.models import Notificacion
from .services import send_push_notification

@receiver(post_save, sender=Evento)
def crear_y_enviar_notificacion_al_publicar(sender, instance, created, **kwargs):
    """
    Esta señal se dispara cada vez que se guarda un objeto Evento.
    Si el evento se publica, crea un objeto Notificacion y dispara el envío.
    """
    def trigger_notification(evento):
        # El usuario que actualizó el evento es el responsable de esta acción.
        audit_user = evento.updated_by
        notificacion = Notificacion.objects.create(
            evento=evento,
            created_by=audit_user,
            updated_by=audit_user
        )
        print(f"Notificación creada para '{evento.titulo}' (ID: {notificacion.id}).")
        
        # TODO: Esta llamada debería ser asíncrona en producción usando Celery.
        # Llamar a esto directamente en el flujo de la petición puede causar lentitud.
        # Ejemplo con Celery: send_push_notification.delay(notificacion.id)
        send_push_notification(notificacion.id)

    # El campo 'update_fields' nos ayuda a saber si 'publicado' fue uno de los campos actualizados.
    is_being_published = instance.publicado and (not kwargs.get('update_fields') or 'publicado' in kwargs['update_fields'])

    if created and instance.publicado:
        # Si el evento se crea como publicado desde el principio
        trigger_notification(instance)
    
    elif not created and is_being_published:
        # Si un evento existente se actualiza para ser publicado
        # Comprobamos si ya existe una notif pendiente para evitar duplicados
        if not Notificacion.objects.filter(evento=instance, estado__in=['pendiente', 'enviado']).exists():
            trigger_notification(instance) 