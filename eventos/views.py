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
    Gestiona los eventos (CRUD) con permisos basados en roles.
    
    Hereda de `AuditModelViewSet` para registrar automáticamente qué usuario
    crea o modifica un evento.
    """
    queryset = Evento.objects.select_related('autor', 'categoria', 'valor').all()
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
            self.permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin', 'QA')]
        else:
            self.permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin', 'QA', 'Trabajador')]
        return super().get_permissions()

@extend_schema(tags=['Eventos'])
class EventoFeedView(generics.ListAPIView):
    """
    Endpoint público para el feed de eventos de la aplicación móvil.

    Retorna una lista de eventos publicados, ordenados con los más recientes
    y los fijados primero.
    """
    queryset = Evento.objects.filter(publicado=True).order_by('-is_pinned', '-fecha')
    serializer_class = EventoSerializer
    permission_classes = [permissions.AllowAny]
