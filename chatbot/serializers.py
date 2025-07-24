from rest_framework import serializers
from .models import ChatbotCategory, ChatbotKnowledgeBase, ChatConversation

class ChatbotCategorySerializer(serializers.ModelSerializer):
    """Serializador para el modelo ChatbotCategory."""
    class Meta:
        model = ChatbotCategory
        fields = ['id', 'name', 'description']

# NUEVO: Serializador simplificado para las preguntas recomendadas.
# Solo necesitamos el ID (para futuras acciones) y el texto de la pregunta.
class RecommendedQuestionSerializer(serializers.ModelSerializer):
    """Serializador para mostrar preguntas recomendadas de forma anidada."""
    class Meta:
        model = ChatbotKnowledgeBase
        fields = ['id', 'question']

class ChatbotKnowledgeBaseSerializer(serializers.ModelSerializer):
    """
    Serializador para la base de conocimiento del chatbot.
    
    Ahora incluye una lista anidada de preguntas recomendadas para guiar
    al usuario en la conversación.
    """
    # Anidamos el serializador de preguntas recomendadas.
    recommended_questions = RecommendedQuestionSerializer(many=True, read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = ChatbotKnowledgeBase
        fields = [
            'id', 'question', 'answer', 'category', 'is_active',
            'recommended_questions',  # Campo anidado
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]

class ChatConversationSerializer(serializers.ModelSerializer):
    """Serializador para el historial de conversaciones."""
    user = serializers.StringRelatedField()
    # Expone la pregunta del conocimiento coincidente para mayor contexto.
    matched_knowledge_question = serializers.CharField(source='matched_knowledge.question', read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ChatConversation
        fields = [
            'id', 'session_id', 'user', 'question_text', 'answer_text',
            'matched_knowledge', 'matched_knowledge_question',
            'created_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['created_at', 'created_by', 'updated_by']

class QuestionSerializer(serializers.Serializer):
    """Serializador para validar la pregunta de entrada del usuario."""
    question = serializers.CharField(max_length=500)
    session_id = serializers.CharField(max_length=100, required=False, allow_blank=True)

class AnswerSerializer(serializers.Serializer):
    """Serializador para la respuesta de salida del chatbot."""
    answer = serializers.CharField()
    session_id = serializers.CharField(max_length=100) 