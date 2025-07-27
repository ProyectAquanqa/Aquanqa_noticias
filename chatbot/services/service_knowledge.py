"""Servicio de gestión de conocimiento para el chatbot."""

import logging
from typing import Dict, List
from django.db import transaction, models
from django.core.cache import cache

from ..models import ChatbotKnowledgeBase
from .cache_service import invalidate_frequent_questions_cache

logger = logging.getLogger(__name__)


def obtener_preguntas_frecuentes(limite: int = 10) -> List[Dict]:
    cache_key = f"chatbot:frequent_questions:{limite}"
    cached_result = cache.get(cache_key)
    
    if cached_result:
        return cached_result
    
    try:
        preguntas = ChatbotKnowledgeBase.objects.filter(
            is_active=True
        ).select_related('category').order_by('-view_count')[:limite]
        
        resultado = [
            {
                'id': p.id,
                'question': p.question,
                'view_count': p.view_count,
                'category': p.category.name if p.category else None
            }
            for p in preguntas
        ]
        
        cache.set(cache_key, resultado, 1800)
        return resultado
    except Exception as e:
        logger.error(f"Error obteniendo preguntas frecuentes: {e}")
        return []


def obtener_preguntas_recomendadas(knowledge_item: ChatbotKnowledgeBase) -> List[Dict]:
    try:
        preguntas = knowledge_item.recommended_questions.filter(is_active=True)
        return [
            {
                'id': p.id, 
                'question': p.question,
                'category': p.category.name if p.category else None
            } 
            for p in preguntas
        ]
    except Exception as e:
        logger.warning(f"Error obteniendo preguntas recomendadas: {e}")
        return []


@transaction.atomic
def incrementar_vistas_knowledge(knowledge_item: ChatbotKnowledgeBase) -> None:
    try:
        ChatbotKnowledgeBase.objects.filter(
            id=knowledge_item.id
        ).update(view_count=models.F('view_count') + 1)
        
        invalidate_frequent_questions_cache()
    except Exception as e:
        logger.warning(f"Error incrementando vistas: {e}")


_incrementar_vistas = incrementar_vistas_knowledge
_obtener_preguntas_recomendadas = obtener_preguntas_recomendadas 