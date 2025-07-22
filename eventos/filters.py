from django_filters import rest_framework as filters
from .models import Evento

class EventoFilter(filters.FilterSet):
    """
    Filtros personalizados para el `EventoViewSet`.

    Permite filtrar por nombre de categoría y si un evento es un reconocimiento.
    """
    # Filtra por el nombre de la categoría, sin ser sensible a mayúsculas.
    categoria_nombre = filters.CharFilter(field_name='categoria__nombre', lookup_expr='iexact')
    
    # Filtra eventos que son reconocimientos (tienen un 'valor' asociado).
    es_reconocimiento = filters.BooleanFilter(field_name='valor', lookup_expr='isnull', exclude=True)

    class Meta:
        model = Evento
        fields = {
            'autor': ['exact'],
            'publicado': ['exact'],
            'is_pinned': ['exact'],
            'categoria': ['exact'], # Filtra por ID de categoría
        } 