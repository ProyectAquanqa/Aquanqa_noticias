from rest_framework import serializers
from .models import Notificacion, DeviceToken

class DeviceTokenSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo DeviceToken.
    """
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = DeviceToken
        fields = ['id', 'token', 'device_type', 'is_active', 'created_at', 'created_by', 'updated_by']
        read_only_fields = ['created_at', 'created_by', 'updated_by']

class NotificacionSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Notificacion.
    """
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Notificacion
        fields = '__all__'
        read_only_fields = ('created_at', 'created_by', 'updated_by') 