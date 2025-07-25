from django.db import models
from django.conf import settings
from core.models import BaseModelWithAudit
import uuid

# Create your models here.
class ChatbotCategory(BaseModelWithAudit):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Categoría de Chatbot"
        verbose_name_plural = "Categorías de Chatbot"

    def __str__(self):
        return self.name

class ChatbotKnowledgeBase(BaseModelWithAudit):
    category = models.ForeignKey(ChatbotCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Categoría")
    question = models.CharField(max_length=255, unique=True)
    answer = models.TextField()
    keywords = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0, verbose_name="Vistas")
    question_embedding = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Vector de la Pregunta (Embedding)",
        help_text="El vector semántico de la pregunta, pre-calculado para búsquedas rápidas."
    )
    recommended_questions = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        verbose_name="Preguntas Recomendadas"
    )

    class Meta:
        verbose_name = "Base de Conocimiento del Chatbot"
        verbose_name_plural = "Bases de Conocimiento del Chatbot"
        ordering = ['-view_count']

    def __str__(self):
        return self.question

class ChatConversation(BaseModelWithAudit):
    session_id = models.CharField(max_length=255, default=uuid.uuid4, verbose_name="ID de Sesión")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuario"
    )
    question_text = models.TextField(verbose_name="Texto de la Pregunta")
    answer_text = models.TextField(verbose_name="Texto de la Respuesta")
    matched_knowledge = models.ForeignKey(
        ChatbotKnowledgeBase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Conocimiento Coincidente"
    )

    class Meta:
        verbose_name = "Conversación de Chat"
        verbose_name_plural = "Conversaciones de Chat"
        ordering = ['-created_at']

    def __str__(self):
        user_display = self.user.username if self.user else "Anónimo"
        return f"Conversación con {user_display} a las {self.created_at.strftime('%Y-%m-%d %H:%M')}"
