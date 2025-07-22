from django.db import models
from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema

from .models import Notificacion, DeviceToken
from .serializers import NotificacionSerializer, DeviceTokenSerializer
from core.permissions import IsOwner
from core.viewsets import AuditModelViewSet

@extend_schema(tags=['Notificaciones'])
class DeviceTokenViewSet(AuditModelViewSet):
    """
    Gestiona los tokens de dispositivo (DeviceTokens) para notificaciones push.

    Permite a un usuario registrar su dispositivo, y ver o eliminar sus
    propios tokens. No permite ver tokens de otros usuarios.
    """
    queryset = DeviceToken.objects.all()
    serializer_class = DeviceTokenSerializer

    def get_queryset(self):
        """Filtra los tokens para devolver solo los del usuario autenticado."""
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Registra un token para el usuario actual.

        Si el token ya existe para el usuario, lo reactiva.
        Si no existe, lo crea. Esto previene duplicados.
        """
        token = serializer.validated_data.get('token')
        device_type = serializer.validated_data.get('device_type')
        
        # Usar get_or_create para manejar tokens existentes.
        instance, created = DeviceToken.objects.get_or_create(
            user=self.request.user, 
            token=token,
            defaults={
                'device_type': device_type, 
                'created_by': self.request.user,
                'updated_by': self.request.user
            }
        )
        
        # Si el token ya existía pero estaba inactivo, se reactiva.
        if not created and not instance.is_active:
            instance.is_active = True
            instance.updated_by = self.request.user
            instance.save(update_fields=['is_active', 'updated_by'])

        serializer.instance = instance

    def get_permissions(self):
        """
        Define permisos por acción:
        - `create`, `list`: Cualquier usuario autenticado.
        - `retrieve`, `update`, `destroy`: Solo el propietario del token.
        """
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated, IsOwner]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()


@extend_schema(tags=['Notificaciones'])
class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Expone el historial de notificaciones para el usuario autenticado.
    
    Un usuario puede ver sus notificaciones directas y las de tipo 'broadcast'.
    """
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filtra las notificaciones para el usuario actual.

        Incluye notificaciones donde el usuario es el destinatario directo
        o aquellas sin destinatario (broadcast).
        """
        user = self.request.user
        return Notificacion.objects.filter(
            models.Q(destinatario=user) | models.Q(destinatario__isnull=True)
        ).select_related('evento').order_by('-created_at')
