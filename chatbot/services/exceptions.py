"""Excepciones del chatbot."""

class ChatbotServiceError(Exception):
    """Clase base para errores en servicios del chatbot."""
    pass

class ModelNotAvailableError(ChatbotServiceError):
    """Lanzada cuando el modelo de IA no está disponible."""
    pass

class NoKnowledgeBaseError(ChatbotServiceError):
    """Lanzada cuando no hay base de conocimiento disponible."""
    pass

class InvalidQuestionError(ChatbotServiceError):
    """Lanzada cuando la pregunta es inválida."""
    pass

class RateLimitError(ChatbotServiceError):
    """Lanzada cuando se excede el límite de consultas."""
    pass

class CacheError(ChatbotServiceError):
    """Lanzada cuando hay problemas con el sistema de caché."""
    pass

class ConversationError(ChatbotServiceError):
    """Lanzada cuando hay problemas registrando conversaciones."""
    pass

class KnowledgeBaseError(ChatbotServiceError):
    """Lanzada cuando hay problemas con la base de conocimiento."""
    pass 