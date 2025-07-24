from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModelWithAudit

class ChatbotCategory(BaseModelWithAudit):
    """
    Agrupa las entradas de la base de conocimiento del chatbot por temas.

    Permite organizar las preguntas y respuestas, por ejemplo, en categorías
    como "Facturación", "Soporte Técnico" o "Información General".
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Categoría de Chatbot"
        verbose_name_plural = "Categorías de Chatbot"
        ordering = ['name']

    def __str__(self):
        return self.name

class ChatbotKnowledgeBase(BaseModelWithAudit):
    """
    Representa una única entrada 'pregunta-respuesta' en la base de conocimiento.

    Cada instancia es una unidad de información que el chatbot utiliza para
    responder a las preguntas de los usuarios. Ahora también puede recomendar
    otras preguntas para guiar la conversación.
    """
    category = models.ForeignKey(ChatbotCategory, on_delete=models.PROTECT, related_name="knowledge_entries")
    question = models.CharField(max_length=255, unique=True)
    answer = models.TextField()
    keywords = models.TextField(blank=True, help_text="Palabras clave separadas por comas para mejorar la búsqueda.")
    is_active = models.BooleanField(default=True, db_index=True)

    # NUEVO: Campo para enlazar preguntas recomendadas.
    # Permite que una respuesta sugiera proactivamente las siguientes preguntas.
    recommended_questions = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        verbose_name="Preguntas Recomendadas",
        help_text="Selecciona otras preguntas de la base de conocimiento para sugerir después de esta respuesta."
    )

    class Meta:
        verbose_name = "Entrada de Conocimiento"
        verbose_name_plural = "Base de Conocimiento del Chatbot"
        ordering = ['-updated_at']

    def __str__(self):
        return self.question

class ChatConversation(BaseModelWithAudit):
    """
    Almacena una única interacción (pregunta y respuesta) del chatbot.

    Registra cada conversación para fines de auditoría, análisis y mejora
    de la base de conocimiento.
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="chat_conversations")
    session_id = models.CharField(max_length=100, db_index=True, help_text="ID para agrupar interacciones de una misma conversación.")
    question_text = models.TextField()
    answer_text = models.TextField()
    matched_knowledge = models.ForeignKey(ChatbotKnowledgeBase, on_delete=models.SET_NULL, null=True, blank=True, related_name="matched_conversations")

    class Meta:
        verbose_name = "Conversación de Chatbot"
        verbose_name_plural = "Historial de Conversaciones"
        ordering = ['-created_at']

    def __str__(self):
        user_info = self.user.username if self.user else f"Sesión {self.session_id[:8]}"
        return f"Conversación con {user_info} en {self.created_at.strftime('%Y-%m-%d %H:%M')}"
