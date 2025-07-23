from rest_framework import serializers
from .models import ChatbotCategory, ChatbotKnowledgeBase, ChatConversation

class ChatbotCategorySerializer(serializers.ModelSerializer):
    """Serializador para el modelo ChatbotCategory."""
    class Meta:
        model = ChatbotCategory
        fields = ['id', 'name', 'description']

class ChatbotKnowledgeBaseSerializer(serializers.ModelSerializer):
    """Serializador para la base de conocimiento del chatbot."""
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = ChatbotKnowledgeBase
        fields = '__all__'

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

class RecommendedQuestionSerializer(serializers.ModelSerializer):
    """Serializador para devolver únicamente el texto de las preguntas recomendadas."""
    class Meta:
        model = ChatbotKnowledgeBase
        fields = ['question'] 