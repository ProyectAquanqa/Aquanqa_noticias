from rest_framework import serializers
from .models import ChatbotCategory, ChatbotKnowledgeBase, ChatConversation

class ChatbotCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatbotCategory
        fields = ['id', 'name', 'description']

class ChatbotKnowledgeBaseSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = ChatbotKnowledgeBase
        fields = '__all__'

class ChatConversationSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
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
    question = serializers.CharField(max_length=500)
    session_id = serializers.CharField(max_length=100, required=False, allow_blank=True) # Para identificar la conversación

class AnswerSerializer(serializers.Serializer):
    answer = serializers.CharField()
    session_id = serializers.CharField(max_length=100) 