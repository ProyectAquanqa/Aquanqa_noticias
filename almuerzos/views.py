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
    ViewSet optimizado para gestión de almuerzos.
    
    Proporciona CRUD completo con permisos basados en roles
    y filtrado avanzado para la API móvil.
    
    Permisos:
    - Lectura: Cualquier usuario autenticado
    - Escritura: Solo Admin y QA
    """
    
    queryset = Almuerzo.objects.all()
    serializer_class = AlmuerzoSerializer
    
    # Configuración de filtros y búsqueda optimizada
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['es_feriado', 'active', 'fecha']
    search_fields = ['entrada', 'plato_fondo', 'refresco', 'dieta']
    ordering_fields = ['fecha']
    ordering = ['fecha']
    
    # Jerarquía por fecha para admin
    date_hierarchy = 'fecha'

    def get_permissions(self):
        """Asigna permisos según la acción."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin', 'QA')]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Listar Almuerzos",
        description="Obtiene lista filtrable de almuerzos con filtros: es_feriado, active, fecha"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Crear Almuerzo (Admin/QA)")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Obtener Almuerzo")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Actualizar Almuerzo (Admin/QA)")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Actualización Parcial (Admin/QA)")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Eliminar Almuerzo (Admin/QA)")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)