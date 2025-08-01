"""
Excepciones personalizadas del módulo chatbot.
"""


class ChatbotServiceError(Exception):
    """Excepción base para errores del servicio de chatbot."""
    pass


class ModelNotAvailableError(ChatbotServiceError):
    """Se lanza cuando el modelo de IA no está disponible."""
    pass


class NoKnowledgeBaseError(ChatbotServiceError):
    """Se lanza cuando no hay base de conocimiento disponible."""
    pass


class InvalidQuestionError(ChatbotServiceError):
    """Se lanza cuando una pregunta es inválida."""
    pass


class RateLimitError(ChatbotServiceError):
    """Se lanza cuando se excede el límite de consultas."""
    pass


# Nuevas excepciones para Knowledge Management
class KnowledgeNotFoundError(ChatbotServiceError):
    """Se lanza cuando no se encuentra una entrada de conocimiento."""
    pass


class CategoryNotFoundError(ChatbotServiceError):
    """Se lanza cuando no se encuentra una categoría."""
    pass


class KnowledgeDuplicateError(ChatbotServiceError):
    """Se lanza cuando se intenta crear una pregunta que ya existe."""
    pass


class InvalidKnowledgeDataError(ChatbotServiceError):
    """Se lanza cuando los datos de conocimiento son inválidos."""
    pass 