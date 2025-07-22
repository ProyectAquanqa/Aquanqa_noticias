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

class NotificacionSerializer(serializers.ModelSerializer):
    """
    Serializador para mostrar el historial de notificaciones a los usuarios.
    """
    evento_titulo = serializers.CharField(source='evento.titulo', read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Notificacion
        fields = ['id', 'evento', 'evento_titulo', 'estado', 'created_at']
        read_only_fields = fields 