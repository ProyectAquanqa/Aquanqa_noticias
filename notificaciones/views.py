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

    @extend_schema(summary="Listar mis Tokens de Dispositivo")
    def list(self, request, *args, **kwargs):
        """Obtiene la lista de tokens de dispositivo registrados por el usuario actual."""
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Registrar un Token de Dispositivo")
    def create(self, request, *args, **kwargs):
        """Registra un nuevo token de dispositivo para el usuario actual."""
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Obtener mi Token de Dispositivo")
    def retrieve(self, request, *args, **kwargs):
        """Obtiene un token de dispositivo específico del usuario actual por su ID."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Actualizar mi Token de Dispositivo")
    def update(self, request, *args, **kwargs):
        """Actualiza un token de dispositivo del usuario actual."""
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Actualización Parcial de mi Token")
    def partial_update(self, request, *args, **kwargs):
        """Actualiza parcialmente un token de dispositivo del usuario actual."""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Eliminar mi Token de Dispositivo")
    def destroy(self, request, *args, **kwargs):
        """Elimina un token de dispositivo del usuario actual."""
        return super().destroy(request, *args, **kwargs)


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

    @extend_schema(summary="Listar mis Notificaciones")
    def list(self, request, *args, **kwargs):
        """Obtiene el historial de notificaciones del usuario (directas y broadcast)."""
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Obtener una Notificación")
    def retrieve(self, request, *args, **kwargs):
        """Obtiene una notificación específica del historial del usuario por su ID."""
        return super().retrieve(request, *args, **kwargs)
