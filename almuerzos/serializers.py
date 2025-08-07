from rest_framework import serializers
from .models import Almuerzo


class AlmuerzoSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para el modelo Almuerzo.
    
    Incluye campos calculados y optimiza la respuesta de la API.
    """
    
    # Campos calculados
    nombre_dia = serializers.SerializerMethodField()
    fecha_formateada = serializers.SerializerMethodField()
    is_available = serializers.ReadOnlyField()
    has_diet_menu = serializers.ReadOnlyField()
    
    # Campos de auditoría como solo lectura
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Almuerzo
        fields = [
            # Información básica
            'id', 'fecha', 'entrada', 'plato_fondo', 'refresco',
            # Control y disponibilidad  
            'es_feriado', 'active', 'link', 'dieta',
            # Campos calculados
            'nombre_dia', 'fecha_formateada', 'is_available', 'has_diet_menu',
            # Auditoría
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'is_available', 'has_diet_menu', 'fecha_formateada'
        ]
    
    def get_nombre_dia(self, obj) -> str:
        """Retorna el nombre del día en español."""
        return obj.nombre_dia()
    
    def get_fecha_formateada(self, obj) -> str:
        """Retorna la fecha formateada como 'Lunes 18 de agosto'."""
        return obj.fecha_formateada()