import firebase_admin
from firebase_admin import messaging
from notificaciones.models import DeviceToken, Notificacion

def send_push_notification(notificacion_id):
    """
    Envía una notificación push a todos los dispositivos activos.
    Maneja el éxito y el fracaso, y desactiva los tokens no válidos.
    """
    try:
        notificacion = Notificacion.objects.get(id=notificacion_id, estado='pendiente')
    except Notificacion.DoesNotExist:
        print(f"No se encontró la notificación pendiente con id={notificacion_id}")
        return

    # 1. Obtener todos los tokens de dispositivos activos
    tokens = list(DeviceToken.objects.filter(is_active=True).values_list('token', flat=True))
    
    if not tokens:
        print("No hay tokens activos para enviar la notificación.")
        notificacion.estado = 'fallido'
        notificacion.error_message = 'No se encontraron tokens activos.'
        notificacion.save()
        return

    # 2. Construir el mensaje de la notificación
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=notificacion.evento.titulo,
            body=notificacion.evento.descripcion[:150] + '...' # Limitar la longitud del cuerpo
        ),
        data={
            'evento_id': str(notificacion.evento.id),
            'click_action': 'FLUTTER_NOTIFICATION_CLICK' # Action para la app móvil
        },
        tokens=tokens,
    )

    # 3. Enviar el mensaje
    try:
        batch_response = messaging.send_multicast(message)
        print(f"Notificaciones enviadas: {batch_response.success_count} con éxito, {batch_response.failure_count} fallaron.")

        # 4. Manejar los envíos fallidos y desactivar tokens inválidos
        if batch_response.failure_count > 0:
            responses = batch_response.responses
            failed_tokens = []
            for idx, response in enumerate(responses):
                if not response.success:
                    token = tokens[idx]
                    failed_tokens.append(token)
                    print(f"Token {token} falló: {response.exception}")
                    # Desactivar tokens que ya no están registrados en FCM
                    if response.exception.code in ('UNREGISTERED', 'INVALID_ARGUMENT'):
                         DeviceToken.objects.filter(token=token).update(is_active=False)

            notificacion.error_message = f"Fallaron {len(failed_tokens)} tokens: {', '.join(failed_tokens)}"
        
        # Marcar la notificación como enviada si al menos una tuvo éxito
        if batch_response.success_count > 0:
            notificacion.estado = 'enviado'
        else:
            notificacion.estado = 'fallido'
        
        notificacion.save()

    except Exception as e:
        print(f"Error al enviar la notificación push: {e}")
        notificacion.estado = 'fallido'
        notificacion.error_message = str(e)
        notificacion.save() 