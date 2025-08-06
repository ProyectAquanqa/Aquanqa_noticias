from rest_framework import permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from .models import Almuerzo
from .serializers import AlmuerzoSerializer
from core.permissions import IsInGroup
from core.viewsets import AuditModelViewSet


@extend_schema(tags=['Almuerzos'])
class AlmuerzoViewSet(AuditModelViewSet):
    """
    Gestiona los menús diarios de almuerzo (CRUD) con permisos basados en roles.
    
    Hereda de `AuditModelViewSet` para registrar automáticamente qué usuario
    crea o modifica un almuerzo.
    
    Permisos:
    - Lectura (list, retrieve): Cualquier usuario autenticado
    - Escritura (create, update, destroy): Solo usuarios en grupos 'Admin' o 'QA'
    
    Funcionalidades:
    - Filtrado por es_feriado, active y fecha
    - Búsqueda en campos entrada, plato_fondo, refresco
    - Ordenamiento por fecha (ascendente por defecto)
    """
    queryset = Almuerzo.objects.all()
    serializer_class = AlmuerzoSerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['entrada', 'plato_fondo', 'refresco']
    filterset_fields = ['es_feriado', 'active', 'fecha']
    ordering_fields = ['fecha']
    ordering = ['fecha']

    def get_permissions(self):
        """
        Asigna permisos basados en la acción solicitada.

        - Escritura (create, update, destroy): Solo 'Admin' y 'QA'.
        - Lectura (list, retrieve): Cualquier usuario autenticado.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin', 'QA')]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() if isinstance(permission, type) else permission for permission in permission_classes]

    @extend_schema(summary="Listar Almuerzos")
    def list(self, request, *args, **kwargs):
        """
        Obtiene una lista filtrable de almuerzos.
        
        Soporta filtrado por:
        - es_feriado: true/false para filtrar por días feriados
        - active: true/false para filtrar por almuerzos activos/inactivos
        - fecha: fecha específica en formato YYYY-MM-DD
        
        Soporta búsqueda en campos entrada, plato_fondo y refresco.
        Ordenado por fecha ascendente por defecto.
        """
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Crear un Almuerzo (Admin/QA)")
    def create(self, request, *args, **kwargs):
        """Crea un nuevo almuerzo. Requiere permisos de Admin o QA."""
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Obtener un Almuerzo")
    def retrieve(self, request, *args, **kwargs):
        """Obtiene los detalles de un almuerzo específico por su ID."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Actualizar un Almuerzo (Admin/QA)")
    def update(self, request, *args, **kwargs):
        """Actualiza completamente un almuerzo existente. Requiere permisos de Admin o QA."""
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Actualización Parcial de un Almuerzo (Admin/QA)")
    def partial_update(self, request, *args, **kwargs):
        """Actualiza parcialmente un almuerzo existente. Requiere permisos de Admin o QA."""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Eliminar un Almuerzo (Admin/QA)")
    def destroy(self, request, *args, **kwargs):
        """Elimina un almuerzo existente. Requiere permisos de Admin o QA."""
        return super().destroy(request, *args, **kwargs)