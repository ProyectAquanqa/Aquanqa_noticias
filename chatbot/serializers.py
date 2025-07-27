"""
Serializers del módulo chatbot.
"""

from rest_framework import serializers
from .models import ChatbotKnowledgeBase, ChatbotCategory, ChatConversation


class ChatbotQuerySerializer(serializers.Serializer):
    question = serializers.CharField(max_length=500, min_length=3)
    session_id = serializers.CharField(max_length=255, required=False, default='anonymous')
    use_cache = serializers.BooleanField(default=True, required=False)

    def validate_question(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("La pregunta no puede estar vacía.")
        
        value = value.strip()
        
        if len(value) < 3:
            raise serializers.ValidationError("La pregunta debe tener al menos 3 caracteres.")
        
        if not any(c.isalpha() for c in value):
            raise serializers.ValidationError("La pregunta debe contener al menos una letra.")
        
        return value


class ChatbotKnowledgeBaseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    recommended_questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatbotKnowledgeBase
        fields = [
            'id', 'category', 'category_name', 'question', 'answer', 'keywords',
            'is_active', 'view_count', 'recommended_questions', 'recommended_questions_count',
            'created_by', 'created_by_username', 'updated_by', 'updated_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'view_count', 'created_by', 'updated_by', 'created_at', 'updated_at']

    def get_recommended_questions_count(self, obj):
        return obj.recommended_questions.filter(is_active=True).count()

    def validate_question(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("La pregunta no puede estar vacía.")
        
        queryset = ChatbotKnowledgeBase.objects.filter(question=value.strip())
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("Ya existe una pregunta con este texto.")
        
        return value.strip()

    def validate_answer(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("La respuesta no puede estar vacía.")
        
        if len(value.strip()) < 10:
            raise serializers.ValidationError("La respuesta debe tener al menos 10 caracteres.")
        
        return value.strip()


class RecommendedQuestionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = ChatbotKnowledgeBase
        fields = ['id', 'question', 'category_name', 'view_count']


class ChatConversationSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    matched_question = serializers.CharField(source='matched_knowledge.question', read_only=True)
    matched_category = serializers.CharField(source='matched_knowledge.category.name', read_only=True)
    conversation_date = serializers.DateTimeField(source='created_at', read_only=True, format='%Y-%m-%d %H:%M:%S')
    
    class Meta:
        model = ChatConversation
        fields = [
            'id', 'session_id', 'user', 'user_username', 'user_full_name',
            'question_text', 'answer_text', 'matched_knowledge', 'matched_question',
            'matched_category', 'conversation_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_full_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return "Usuario Anónimo"


class ChatbotCategorySerializer(serializers.ModelSerializer):
    knowledge_count = serializers.SerializerMethodField()
    active_knowledge_count = serializers.SerializerMethodField()
    total_views = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatbotCategory
        fields = ['id', 'name', 'description', 'knowledge_count', 'active_knowledge_count', 'total_views', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_knowledge_count(self, obj):
        return obj.chatbotknowledgebase_set.count()

    def get_active_knowledge_count(self, obj):
        return obj.chatbotknowledgebase_set.filter(is_active=True).count()

    def get_total_views(self, obj):
        from django.db.models import Sum
        result = obj.chatbotknowledgebase_set.aggregate(total_views=Sum('view_count'))
        return result['total_views'] or 0


class ChatbotStatsSerializer(serializers.Serializer):
    total_conversations = serializers.IntegerField()
    total_knowledge_base = serializers.IntegerField()
    total_views = serializers.IntegerField()
    conversations_today = serializers.IntegerField()
    top_categories = serializers.ListField(child=serializers.DictField())
    average_score = serializers.FloatField(required=False)
    cache_hit_rate = serializers.FloatField(required=False) 