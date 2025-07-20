from rest_framework import serializers
from .models import Evento, Categoria, Valor

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre']

class ValorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Valor
        fields = ['id', 'nombre', 'insignia']

class EventoSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Evento, incluyendo la categoría y el valor.
    """
    autor = serializers.StringRelatedField(read_only=True)
    categoria = CategoriaSerializer(read_only=True)
    valor = ValorSerializer(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    categoria_id = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(), source='categoria', write_only=True
    )
    valor_id = serializers.PrimaryKeyRelatedField(
        queryset=Valor.objects.all(), source='valor', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Evento
        fields = [
            'id', 'titulo', 'descripcion', 'fecha', 'publicado', 'is_pinned',
            'autor', 'imagen', 'categoria', 'valor', 'created_at', 'updated_at',
            'categoria_id', 'valor_id', 'created_by', 'updated_by'
        ]
        read_only_fields = ['autor', 'created_at', 'updated_at', 'created_by', 'updated_by']
        extra_kwargs = {
            'imagen': {'required': False}
        }
    
    def create(self, validated_data):
        """
        Asigna el usuario actual como autor al crear el evento.
        """
        validated_data['autor'] = self.context['request'].user
        return super().create(validated_data) 