from django.db import models
from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema

from .models import Notificacion, DeviceToken
from .serializers import NotificacionSerializer, DeviceTokenSerializer
from core.permissions import IsOwner

@extend_schema(tags=['Notificaciones'])
class DeviceTokenViewSet(viewsets.ModelViewSet):
    """
    API endpoint para registrar y eliminar tokens de dispositivos (DeviceToken).
    Un usuario solo puede ver y gestionar sus propios tokens.
    """
    queryset = DeviceToken.objects.all()
    serializer_class = DeviceTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Esta vista solo debe devolver los tokens del usuario que hace la petición.
        """
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Asigna el usuario actual al crear un nuevo token.
        Utiliza get_or_create para evitar tokens duplicados por usuario.
        Esta lógica es personalizada y no usa AuditModelViewSet.
        """
        token = serializer.validated_data.get('token')
        device_type = serializer.validated_data.get('device_type', 'android')
        
        instance, created = DeviceToken.objects.get_or_create(
            user=self.request.user, 
            token=token,
            defaults={
                'device_type': device_type, 
                'created_by': self.request.user,
                'updated_by': self.request.user
            }
        )
        
        if not created:
            instance.updated_by = self.request.user
            instance.is_active = True
            instance.save(update_fields=['updated_by', 'is_active'])

        # Devolvemos el objeto a través del serializador para la respuesta
        serializer.instance = instance

    def get_permissions(self):
        """
        - Cualquiera autenticado puede crear (registrar) su token.
        - Solo el propietario puede ver, actualizar o eliminar su token.
        """
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOwner()]
        return super().get_permissions()

@extend_schema(tags=['Notificaciones'])
class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint para ver el historial de notificaciones.
    Un usuario solo puede ver las notificaciones que le pertenecen
    o las que son de tipo broadcast (sin destinatario).
    """
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filtra el queryset para devolver solo las notificaciones
        relevantes para el usuario actual (las suyas y las de broadcast).
        """
        if getattr(self, 'swagger_fake_view', False):
            return Notificacion.objects.none()

        user = self.request.user
        return Notificacion.objects.filter(
            models.Q(destinatario=user) | models.Q(destinatario=None)
        ).select_related('evento').order_by('-created_at')
