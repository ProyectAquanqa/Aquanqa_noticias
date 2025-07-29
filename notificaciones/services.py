"""
Módulo de servicios para la gestión de notificaciones.

Este archivo contiene la lógica de negocio para el envío de notificaciones push,
desacoplada de las vistas y modelos.
"""
import logging
import firebase_admin
from firebase_admin import messaging
from .models import DeviceToken, Notificacion

logger = logging.getLogger(__name__)

def send_push_notification(notificacion_id):
    """
    Envía una notificación push a todos los dispositivos activos vía FCM.

    Esta función es llamada por una señal cuando un evento se publica.
    Busca la notificación, obtiene los tokens, construye y envía el mensaje.
    
    Args:
        notificacion_id (int): El ID del objeto Notificacion a enviar.
    """
    try:
        notificacion = Notificacion.objects.get(id=notificacion_id)
    except Notificacion.DoesNotExist:
        logger.error(f"Notificación con id={notificacion_id} no encontrada.")
        return

    # Verificar que no se haya enviado ya
    if notificacion.leido:
        logger.info(f"Notificación con id={notificacion_id} ya fue procesada.")
        return

    tokens = list(DeviceToken.objects.filter(is_active=True).values_list('token', flat=True))
    
    if not tokens:
        logger.warning('No se encontraron tokens de dispositivo activos.')
        notificacion.mensaje = 'No se encontraron tokens de dispositivo activos.'
        notificacion.save()
        return

    # Preparar el contenido de la notificación
    titulo = notificacion.evento.titulo
    descripcion = notificacion.evento.descripcion[:240]  # Límite recomendado para visibilidad
    
    # Actualizar la notificación con el contenido
    notificacion.titulo = titulo
    notificacion.mensaje = descripcion
    
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=titulo,
            body=descripcion
        ),
        data={
            'evento_id': str(notificacion.evento.id),
            'titulo': titulo,
            'tipo': 'nuevo_evento'
        },
        tokens=tokens,
    )

    try:
        batch_response = messaging.send_each_for_multicast(message)
        logger.info(f"Notificaciones enviadas: {batch_response.success_count} éxito, {batch_response.failure_count} fallo.")

        # Manejar tokens que fallaron para desactivarlos si son inválidos
        if batch_response.failure_count > 0:
            _handle_failed_tokens(batch_response, tokens)
        
        # Marcar como procesada
        notificacion.leido = True
        notificacion.datos = {
            'success_count': batch_response.success_count,
            'failure_count': batch_response.failure_count,
            'total_tokens': len(tokens)
        }

    except Exception as e:
        logger.error(f"Error crítico al enviar notificaciones push: {e}")
        notificacion.mensaje = f"Error al enviar: {str(e)}"
    
    notificacion.save()

def _handle_failed_tokens(batch_response, tokens):
    """
    Procesa la respuesta de FCM para desactivar tokens inválidos.
    """
    responses = batch_response.responses
    failed_tokens = []
    
    for idx, response in enumerate(responses):
        if not response.success:
            token = tokens[idx]
            failed_tokens.append(token)
            
            # Si el token es inválido o no registrado, lo desactivamos
            if hasattr(response, 'exception') and response.exception:
                error_code = getattr(response.exception, 'code', None)
                if error_code in ('UNREGISTERED', 'INVALID_ARGUMENT'):
                    DeviceToken.objects.filter(token=token).update(is_active=False)
                    logger.info(f"Token desactivado por ser inválido: {token[:20]}...")

    if failed_tokens:
        logger.warning(f"Fallaron {len(failed_tokens)} tokens de {len(tokens)} totales.") 