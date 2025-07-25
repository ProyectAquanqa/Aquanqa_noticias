from django.contrib import admin
from .models import ChatbotKnowledgeBase, ChatbotCategory, ChatConversation
from core.admin import AuditModelAdmin

@admin.register(ChatbotCategory)
class ChatbotCategoryAdmin(AuditModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)

@admin.register(ChatbotKnowledgeBase)
class ChatbotKnowledgeBaseAdmin(AuditModelAdmin):
    list_display = ('question', 'category', 'view_count', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer', 'keywords')
    autocomplete_fields = ['category', 'recommended_questions']
    filter_horizontal = ('recommended_questions',)

@admin.register(ChatConversation)
class ChatConversationAdmin(AuditModelAdmin):
    list_display = ('__str__', 'user', 'matched_knowledge', 'created_at')
    list_filter = ('user',)
    search_fields = ('question_text', 'answer_text', 'user__username')
    autocomplete_fields = ['user', 'matched_knowledge']
    readonly_fields = ('session_id', 'question_text', 'answer_text', 'matched_knowledge', 'user', 'created_by', 'created_at', 'updated_by', 'updated_at')
