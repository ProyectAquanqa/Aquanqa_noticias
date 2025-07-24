from django.shortcuts import render
from django.db import models
from rest_framework import permissions, generics
from rest_framework.response import Response

from .models import Evento, Categoria
from .serializers import EventoSerializer, CategoriaSerializer
from .filters import EventoFilter
from core.permissions import IsInGroup
from core.viewsets import AuditModelViewSet
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend

# Create your views here.

@extend_schema(tags=['Eventos'])
class EventoViewSet(AuditModelViewSet):
    """
    Gestiona los eventos (CRUD) con permisos basados en roles.
    
    Hereda de `AuditModelViewSet` para registrar automáticamente qué usuario
    crea o modifica un evento.
    """
    # Optimizamos la consulta para incluir el autor y su perfil relacionado
    queryset = Evento.objects.select_related('autor__profile', 'categoria').all()
    serializer_class = EventoSerializer
    filterset_class = EventoFilter
    filter_backends = [filters.OrderingFilter, filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['titulo', 'descripcion']
    ordering_fields = ['fecha', 'publicado', 'is_pinned']
    ordering = ['-is_pinned', '-fecha']

    def get_permissions(self):
        """
        Asigna permisos basados en la acción solicitada.

        - Escritura (create, update, destroy): Solo 'Admin' y 'QA'.
        - Lectura (list, retrieve): 'Admin', 'QA' y 'Trabajador'.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin', 'QA')]
        else:
            permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin', 'QA', 'Trabajador')]
        return [permission() if isinstance(permission, type) else permission for permission in permission_classes]

    @extend_schema(summary="Listar Eventos")
    def list(self, request, *args, **kwargs):
        """Obtiene una lista paginada y filtrable de eventos."""
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Crear un Evento (Admin/QA)")
    def create(self, request, *args, **kwargs):
        """Crea un nuevo evento. Requiere permisos de Admin o QA."""
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Obtener un Evento")
    def retrieve(self, request, *args, **kwargs):
        """Obtiene los detalles de un evento específico por su ID."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Actualizar un Evento (Admin/QA)")
    def update(self, request, *args, **kwargs):
        """Actualiza completamente un evento existente. Requiere permisos de Admin o QA."""
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Actualización Parcial de un Evento (Admin/QA)")
    def partial_update(self, request, *args, **kwargs):
        """Actualiza parcialmente un evento existente. Requiere permisos de Admin o QA."""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Eliminar un Evento (Admin/QA)")
    def destroy(self, request, *args, **kwargs):
        """Elimina un evento existente. Requiere permisos de Admin o QA."""
        return super().destroy(request, *args, **kwargs)


@extend_schema(
    tags=['Eventos'],
    summary="Obtener el Feed de Eventos Públicos",
    description="Obtiene una lista de todos los eventos publicados, ordenados con los más recientes y fijados primero. Este endpoint es público y no requiere autenticación."
)
class EventoFeedView(generics.ListAPIView):
    """
    Endpoint público para el feed de eventos de la aplicación móvil.

    Retorna una lista de eventos publicados, ordenados con los más recientes
    y los fijados primero.
    """
    queryset = Evento.objects.filter(publicado=True).order_by('-is_pinned', '-fecha')
    serializer_class = EventoSerializer
    permission_classes = [permissions.AllowAny]
