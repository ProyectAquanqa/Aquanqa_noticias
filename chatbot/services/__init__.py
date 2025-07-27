"""Servicios del chatbot."""

from .service_statistics import obtener_estadisticas_chatbot
from .service_ai import procesar_consulta_con_ia
from .exceptions import (
    ChatbotServiceError,
    ModelNotAvailableError,
    NoKnowledgeBaseError,
    InvalidQuestionError,
    RateLimitError
)


def procesar_consulta_chatbot(pregunta: str, user_id=None, session_id='anonymous', use_cache=True):
    """Función principal de procesamiento de consultas del chatbot con IA."""
    return procesar_consulta_con_ia(
        pregunta=pregunta,
        user_id=user_id,
        session_id=session_id,
        use_cache=use_cache
    )


def obtener_preguntas_frecuentes(limite=10):
    """Obtiene preguntas frecuentes de la base de conocimiento."""
    from ..models import ChatbotKnowledgeBase
    try:
        preguntas = ChatbotKnowledgeBase.objects.filter(
            is_active=True
        ).select_related('category').order_by('-view_count')[:limite]
        
        return [
            {
                'id': p.id,
                'question': p.question,
                'view_count': p.view_count,
                'category': p.category.name if p.category else None
            }
            for p in preguntas
        ]
    except Exception:
        return [] 