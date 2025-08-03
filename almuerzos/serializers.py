from rest_framework import serializers
from .models import Almuerzo


class AlmuerzoSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Almuerzo.
    
    Incluye un campo calculado 'nombre_dia' que retorna el nombre del día
    en español basado en la fecha del almuerzo. Los campos de auditoría
    se configuran como solo lectura.
    """
    nombre_dia = serializers.SerializerMethodField()
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Almuerzo
        fields = [
            'id', 'fecha', 'entrada', 'plato_fondo', 'refresco', 
            'es_feriado', 'link', 'nombre_dia', 'created_at', 
            'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_nombre_dia(self, obj):
        """
        Retorna el nombre del día en español calculado desde la fecha.
        
        Args:
            obj (Almuerzo): Instancia del modelo Almuerzo
            
        Returns:
            str: Nombre del día de la semana en español
        """
        dias_es = {
            "Monday": "Lunes",
            "Tuesday": "Martes",
            "Wednesday": "Miércoles",
            "Thursday": "Jueves",
            "Friday": "Viernes",
            "Saturday": "Sábado",
            "Sunday": "Domingo"
        }
        return dias_es[obj.fecha.strftime("%A")]