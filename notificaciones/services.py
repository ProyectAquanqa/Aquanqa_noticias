"""
Módulo de servicios para la gestión de notificaciones.

Este archivo contiene la lógica de negocio para el envío de notificaciones push,
desacoplada de las vistas y modelos.
"""
import firebase_admin
from firebase_admin import messaging
from .models import DeviceToken, Notificacion

def send_push_notification(notificacion_id):
    """
    Envía una notificación push a todos los dispositivos activos vía FCM.

    Esta función es llamada por una señal cuando un evento se publica.
    Busca la notificación, obtiene los tokens, construye y envía el mensaje.
    
    Args:
        notificacion_id (int): El ID del objeto Notificacion a enviar.
    """
    try:
        notificacion = Notificacion.objects.get(id=notificacion_id, estado='pendiente')
    except Notificacion.DoesNotExist:
        print(f"Notificación con id={notificacion_id} no encontrada o ya procesada.")
        return

    tokens = list(DeviceToken.objects.filter(is_active=True).values_list('token', flat=True))
    
    if not tokens:
        notificacion.estado = 'fallido'
        notificacion.error_message = 'No se encontraron tokens de dispositivo activos.'
        notificacion.save()
        return

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=notificacion.evento.titulo,
            body=notificacion.evento.descripcion[:240] # Límite recomendado para visibilidad
        ),
        data={'evento_id': str(notificacion.evento.id)},
        tokens=tokens,
    )

    try:
        batch_response = messaging.send_multicast(message)
        print(f"Notificaciones enviadas: {batch_response.success_count} éxito, {batch_response.failure_count} fallo.")

        # Manejar tokens que fallaron para desactivarlos si son inválidos.
        if batch_response.failure_count > 0:
            _handle_failed_tokens(batch_response, tokens, notificacion)
        
        notificacion.estado = 'enviado' if batch_response.success_count > 0 else 'fallido'

    except Exception as e:
        print(f"Error crítico al enviar notificaciones push: {e}")
        notificacion.estado = 'fallido'
        notificacion.error_message = str(e)
    
    notificacion.save()

def _handle_failed_tokens(batch_response, tokens, notificacion):
    """
    Procesa la respuesta de FCM para desactivar tokens inválidos.
    """
    responses = batch_response.responses
    failed_tokens = []
    for idx, response in enumerate(responses):
        if not response.success:
            token = tokens[idx]
            failed_tokens.append(token)
            
            # Si el token es inválido o no registrado, lo desactivamos.
            error_code = response.exception.code
            if error_code in ('UNREGISTERED', 'INVALID_ARGUMENT'):
                 DeviceToken.objects.filter(token=token).update(is_active=False)

    notificacion.error_message = f"Fallaron {len(failed_tokens)} tokens." 