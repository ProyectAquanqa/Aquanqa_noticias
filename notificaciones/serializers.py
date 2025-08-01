from rest_framework import serializers
from .models import Notificacion, DeviceToken

class DeviceTokenSerializer(serializers.ModelSerializer):
    """
    Serializador para registrar y gestionar los tokens de los dispositivos.
    """
    class Meta:
        model = DeviceToken
        fields = ['id', 'token', 'device_type']
        read_only_fields = ['id']

class EventoNotificacionSerializer(serializers.ModelSerializer):
    """
    Serializador simplificado para eventos en notificaciones.
    """
    autor = serializers.SerializerMethodField()
    
    class Meta:
        from eventos.models import Evento
        model = Evento
        fields = ['id', 'titulo', 'autor']
    
    def get_autor(self, obj):
        if hasattr(obj, 'created_by') and obj.created_by:
            return {
                'id': obj.created_by.id,
                'full_name': f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.username,
                'foto_perfil': getattr(obj.created_by, 'foto_perfil', None)
            }
        return None

class NotificacionSerializer(serializers.ModelSerializer):
    """
    Serializador para mostrar el historial de notificaciones a los usuarios.
    Compatible con el formato esperado por la app Android.
    """
    evento = EventoNotificacionSerializer(read_only=True)
    fecha_creacion = serializers.DateTimeField(source='created_at', read_only=True)
    leida = serializers.BooleanField(default=False)
    tipo = serializers.SerializerMethodField()

    class Meta:
        model = Notificacion
        fields = ['id', 'titulo', 'mensaje', 'fecha_creacion', 'leida', 'tipo', 'evento']
        read_only_fields = ['id', 'titulo', 'mensaje', 'fecha_creacion', 'tipo', 'evento']
    
    def get_tipo(self, obj):
        """Determina el tipo de notificación basado en si tiene evento asociado."""
        return 'evento' if obj.evento else 'general'