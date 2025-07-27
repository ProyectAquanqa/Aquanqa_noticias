"""Servicio de caché para el chatbot."""

import hashlib
from typing import Dict, Optional
from django.core.cache import cache

CACHE_TIMEOUT = 3600
CACHE_PREFIX = 'chatbot'


def _generate_cache_key(question: str) -> str:
    question_hash = hashlib.md5(question.lower().encode()).hexdigest()
    return f"{CACHE_PREFIX}:query:{question_hash}"


def get_cached_response(question: str) -> Optional[Dict]:
    cache_key = _generate_cache_key(question)
    return cache.get(cache_key)


def set_cached_response(question: str, response: Dict) -> None:
    cache_key = _generate_cache_key(question)
    cache.set(cache_key, response, CACHE_TIMEOUT)


def clear_chatbot_cache() -> None:
    try:
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern(f"{CACHE_PREFIX}:*")
    except (AttributeError, Exception):
        pass


def invalidate_frequent_questions_cache() -> None:
    try:
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern(f"{CACHE_PREFIX}:frequent_questions:*")
    except (AttributeError, Exception):
        pass


def invalidate_stats_cache() -> None:
    cache.delete(f"{CACHE_PREFIX}:stats") 