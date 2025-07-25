from rest_framework import serializers
from .models import Evento, Categoria
from django.contrib.auth import get_user_model

User = get_user_model()

class CategoriaSerializer(serializers.ModelSerializer):
    """Serializador para el modelo Categoria."""
    class Meta:
        model = Categoria
        fields = ['id', 'nombre']

class AutorSerializer(serializers.ModelSerializer):
    """
    Serializador ligero para mostrar la información del autor de un evento.
    Incluye el nombre completo y la URL de la foto de perfil.
    """
    full_name = serializers.SerializerMethodField()
    foto_perfil = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'foto_perfil']

    def get_full_name(self, obj):
        """Devuelve el nombre completo del usuario."""
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_foto_perfil(self, obj):
        """
        Devuelve la URL completa de la foto de perfil.
        Accede directamente al campo 'foto_perfil' del objeto de usuario.
        """
        request = self.context.get('request')
        if obj.foto_perfil and hasattr(obj.foto_perfil, 'url') and request:
            return request.build_absolute_uri(obj.foto_perfil.url)
        return None

class EventoSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Evento.
    
    Maneja la representación de relaciones (autor, categoría) para lectura
    y acepta IDs para escritura, facilitando la creación y actualización de eventos.
    """
    # Usamos el AutorSerializer para anidar la información del autor.
    autor = AutorSerializer(read_only=True)
    categoria = CategoriaSerializer(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    # Campos de solo escritura para recibir IDs al crear/actualizar.
    categoria_id = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(), source='categoria', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Evento
        fields = [
            'id', 'titulo', 'descripcion', 'fecha', 'publicado', 'is_pinned',
            'autor', 'imagen', 'categoria', 'created_at', 'updated_at',
            'categoria_id', 'created_by', 'updated_by'
        ]
        read_only_fields = ['autor', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def create(self, validated_data):
        """Asigna el usuario de la petición como autor del evento."""
        validated_data['autor'] = self.context['request'].user
        return super().create(validated_data) 