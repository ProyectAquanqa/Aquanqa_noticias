"""Servicio de conversaciones para el chatbot."""

import logging
from typing import Optional
from django.contrib.auth import get_user_model

from ..models import ChatbotKnowledgeBase, ChatConversation
from .cache_service import invalidate_stats_cache

logger = logging.getLogger(__name__)
User = get_user_model()


def registrar_conversacion(session_id: str, user_id: Optional[int], question_text: str, 
                          answer_text: str, matched_knowledge: Optional[ChatbotKnowledgeBase]) -> None:
    try:
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.warning(f"Usuario con ID {user_id} no encontrado")
        
        ChatConversation.objects.create(
            session_id=session_id,
            user=user,
            question_text=question_text,
            answer_text=answer_text,
            matched_knowledge=matched_knowledge
        )
        invalidate_stats_cache()
    except Exception as e:
        logger.error(f"Error registrando conversación: {e}")


def obtener_historial_conversaciones(user_id: Optional[int] = None, limit: int = 50):
    try:
        queryset = ChatConversation.objects.select_related(
            'user', 'matched_knowledge'
        ).order_by('-created_at')
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset[:limit]
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}")
        return []


_registrar_conversacion = registrar_conversacion 