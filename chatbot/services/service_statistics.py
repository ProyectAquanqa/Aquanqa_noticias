"""Servicio de estadísticas para el chatbot."""

import logging
from typing import Dict
from django.core.cache import cache
from django.db.models import Count, Sum
from django.utils import timezone

from ..models import ChatbotKnowledgeBase, ChatConversation

logger = logging.getLogger(__name__)


def obtener_estadisticas_chatbot() -> Dict:
    cache_key = "chatbot:stats"
    cached_stats = cache.get(cache_key)
    
    if cached_stats:
        return cached_stats
    
    try:
        stats = {
            'total_conversations': ChatConversation.objects.count(),
            'total_knowledge_base': ChatbotKnowledgeBase.objects.filter(is_active=True).count(),
            'total_views': ChatbotKnowledgeBase.objects.aggregate(
                total=Sum('view_count')
            )['total'] or 0,
            'conversations_today': ChatConversation.objects.filter(
                created_at__date=timezone.now().date()
            ).count(),
            'top_categories': list(
                ChatbotKnowledgeBase.objects.filter(is_active=True)
                .values('category__name')
                .annotate(count=Count('id'))
                .order_by('-count')[:5]
            )
        }
        
        cache.set(cache_key, stats, 900)
        return stats
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return {}


def obtener_metricas_rendimiento() -> Dict:
    try:
        return {
            'cache_enabled': True,
            'model_loaded': True,
            'avg_response_time': 0.5,
        }
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {e}")
        return {} 