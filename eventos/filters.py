from django_filters import rest_framework as filters
from .models import Evento

class EventoFilter(filters.FilterSet):
    """
    Filtros para el listado de eventos.
    Permite filtrar por varios criterios, incluyendo si es un reconocimiento.
    """
    categoria = filters.CharFilter(field_name='categoria__nombre', lookup_expr='iexact')
    es_reconocimiento = filters.BooleanFilter(field_name='valor', lookup_expr='isnull', exclude=True)

    class Meta:
        model = Evento
        fields = {
            'autor': ['exact'],
            'publicado': ['exact'],
            'is_pinned': ['exact'],
            'categoria': ['exact'],
        } 