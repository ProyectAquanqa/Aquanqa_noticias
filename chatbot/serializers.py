from rest_framework import serializers
from .models import ChatbotKnowledgeBase, ChatConversation

class ChatbotQuerySerializer(serializers.Serializer):
    """
    Serializador para validar la pregunta entrante del usuario.
    """
    question = serializers.CharField(max_length=500)
    
class RecommendedQuestionSerializer(serializers.ModelSerializer):
    """
    Serializador simplificado para las preguntas recomendadas.
    """
    class Meta:
        model = ChatbotKnowledgeBase
        fields = ['id', 'question']

class ChatbotKnowledgeBaseSerializer(serializers.ModelSerializer):
    """
    Serializador completo para la gestión de la base de conocimiento en el admin.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    recommended_questions = RecommendedQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = ChatbotKnowledgeBase
        fields = (
            'id', 'question', 'answer', 'category', 'category_name',
            'keywords', 'view_count', 'is_active', 'recommended_questions'
        )
        read_only_fields = ('view_count',)

class ChatConversationSerializer(serializers.ModelSerializer):
    """
    Serializador para mostrar el historial de conversaciones.
    """
    user_username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    matched_question = serializers.CharField(source='matched_knowledge.question', read_only=True, allow_null=True)

    class Meta:
        model = ChatConversation
        fields = (
            'id', 'session_id', 'user_username', 'question_text',
            'answer_text', 'matched_knowledge', 'matched_question', 'created_at'
        ) 