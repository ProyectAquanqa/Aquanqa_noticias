from django.shortcuts import render
from django.db import models
from rest_framework import permissions, generics
from rest_framework.response import Response

from .models import Evento, Valor, Categoria
from .serializers import EventoSerializer, CategoriaSerializer, ValorSerializer
from .filters import EventoFilter
from core.permissions import IsInGroup
from core.viewsets import AuditModelViewSet
from drf_spectacular.utils import extend_schema
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend

# Create your views here.

@extend_schema(tags=['Eventos'])
class EventoViewSet(AuditModelViewSet):
    """
    API endpoint que permite ver, crear, editar y eliminar Eventos.
    Los permisos se basan en los roles: Admin, QA, Trabajador.
    La auditoría de usuarios (quién creó/modificó) es automática.
    """
    queryset = Evento.objects.all().select_related('autor', 'categoria', 'valor', 'created_by', 'updated_by')
    serializer_class = EventoSerializer
    filterset_class = EventoFilter
    filter_backends = [filters.OrderingFilter, filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['titulo', 'descripcion']
    ordering_fields = ['fecha', 'publicado', 'is_pinned']
    ordering = ['-is_pinned', '-fecha']

    def get_permissions(self):
        """
        Asigna permisos basados en la acción.
        - Escritura (CUD): solo Admin y QA.
        - Lectura (GET): Admin, QA y Trabajador.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin', 'QA')]
        else: # list, retrieve
            permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin', 'QA', 'Trabajador')]
        return [permission for permission in permission_classes]

    # El método perform_create se elimina para que se utilice
    # la implementación de AuditModelViewSet, que ya se encarga de
    # created_by y updated_by. El campo 'autor' se gestionará en el serializador.

@extend_schema(tags=['Eventos'])
class EventoFeedView(generics.ListAPIView):
    """
    Endpoint público para el feed de la app móvil.
    Devuelve solo eventos publicados, ordenados por fecha descendente.
    """
    queryset = Evento.objects.filter(publicado=True).order_by('-fecha')
    serializer_class = EventoSerializer
    permission_classes = [permissions.AllowAny]
