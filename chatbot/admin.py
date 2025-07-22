from django.contrib import admin
from .models import ChatbotCategory, ChatbotKnowledgeBase, ChatConversation
from core.admin import AuditModelAdmin

@admin.register(ChatbotCategory)
class ChatbotCategoryAdmin(AuditModelAdmin):
    """Interfaz administrativa para las categorías del chatbot."""
    list_display = ('name', 'description', 'created_at', 'updated_at', 'created_by', 'updated_by')
    search_fields = ('name', 'description')
    readonly_fields = ('created_by', 'updated_by')

@admin.register(ChatbotKnowledgeBase)
class ChatbotKnowledgeBaseAdmin(AuditModelAdmin):
    """Interfaz administrativa para la base de conocimiento del chatbot."""
    list_display = ('question', 'category', 'is_active', 'updated_at', 'updated_by')
    list_filter = ('is_active', 'category', 'updated_at')
    search_fields = ('question', 'answer', 'keywords')
    autocomplete_fields = ['category']  # Mejora la selección de categorías
    readonly_fields = ('created_by', 'updated_by')

@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    """
    Interfaz de solo lectura para el historial de conversaciones del chatbot.

    Permite a los administradores revisar las interacciones de los usuarios
    sin permitir la modificación o creación de registros.
    """
    list_display = ('__str__', 'user', 'session_id', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('question_text', 'answer_text', 'user__username', 'session_id')
    readonly_fields = ('user', 'session_id', 'question_text', 'answer_text', 'matched_knowledge', 'created_at', 'updated_at', 'created_by', 'updated_by')
    
    def has_change_permission(self, request, obj=None):
        """Impide la modificación de historiales de chat desde el admin."""
        return False

    def has_add_permission(self, request):
        """Impide la creación de nuevas conversaciones desde el admin."""
        return False
