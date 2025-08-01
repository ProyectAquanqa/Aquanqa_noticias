"""
Servicio de IA para el chatbot.
"""

import logging
import hashlib
import numpy as np
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from sentence_transformers import SentenceTransformer, util
import torch

from ..models import ChatbotKnowledgeBase, ChatConversation

logger = logging.getLogger(__name__)

MODEL_NAME = 'hiiamsid/sentence_similarity_spanish_es'
SIMILARITY_THRESHOLD = 0.5  #  permite más coincidencias
KEYWORD_MINIMUM_SCORE = 0.2  # Score mínimo para búsqueda por keywords
CACHE_TIMEOUT = 3600
CACHE_PREFIX = 'chatbot'


class ChatbotServiceError(Exception):
    pass

class ModelNotAvailableError(ChatbotServiceError):
    pass

class NoKnowledgeBaseError(ChatbotServiceError):
    pass

class InvalidQuestionError(ChatbotServiceError):
    pass

class RateLimitError(ChatbotServiceError):
    pass


class ChatbotModelManager:
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._load_model()
        return cls._instance
    
    @classmethod
    def _load_model(cls):
        try:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(f"Cargando modelo '{MODEL_NAME}' en {device}")
            cls._model = SentenceTransformer(MODEL_NAME, device=device)
            logger.info("Modelo cargado exitosamente.")
        except Exception as e:
            logger.error(f"Error al cargar modelo: {e}")
            cls._model = None
    
    @property
    def model(self):
        return self._model
    
    def is_available(self) -> bool:
        return self._model is not None


_model_manager = ChatbotModelManager()


def _generate_cache_key(question: str) -> str:
    question_hash = hashlib.md5(question.lower().encode()).hexdigest()
    return f"{CACHE_PREFIX}:query:{question_hash}"

def _get_cached_response(question: str) -> Optional[Dict]:
    cache_key = _generate_cache_key(question)
    return cache.get(cache_key)

def _set_cached_response(question: str, response: Dict) -> None:
    cache_key = _generate_cache_key(question)
    cache.set(cache_key, response, CACHE_TIMEOUT)


def _buscar_por_keywords(pregunta: str) -> Tuple[Optional[ChatbotKnowledgeBase], float]:
    """
    Busca coincidencias usando palabras clave en preguntas, respuestas y keywords.
    """
    import re
    from django.db.models import Q
    
    # Normalizar la pregunta del usuario
    pregunta_limpia = re.sub(r'[¿?¡!.,;:]', '', pregunta.lower()).strip()
    palabras_usuario = set(pregunta_limpia.split())
    
    # Filtrar palabras muy cortas o comunes
    palabras_filtradas = {p for p in palabras_usuario if len(p) > 2 and p not in ['que', 'como', 'donde', 'cuando', 'por', 'para', 'con', 'sin', 'del', 'las', 'los', 'una', 'uno', 'esta', 'este', 'son', 'hay', 'muy', 'mas', 'pero']}
    
    if not palabras_filtradas:
        return None, 0.0
    
    # Buscar en la base de conocimiento activa
    knowledge_items = ChatbotKnowledgeBase.objects.filter(is_active=True)
    
    mejor_match = None
    mejor_score = 0.0
    
    for item in knowledge_items:
        score = 0.0
        total_palabras = len(palabras_filtradas)
        
        # Buscar en la pregunta
        pregunta_item = re.sub(r'[¿?¡!.,;:]', '', item.question.lower())
        palabras_pregunta = set(pregunta_item.split())
        coincidencias_pregunta = palabras_filtradas.intersection(palabras_pregunta)
        score += len(coincidencias_pregunta) * 0.4  # 40% por coincidencias en pregunta
        
        # Buscar en keywords específicas
        if item.keywords:
            keywords_item = set(item.keywords.lower().replace(',', ' ').split())
            coincidencias_keywords = palabras_filtradas.intersection(keywords_item)
            score += len(coincidencias_keywords) * 0.5  # 50% por coincidencias en keywords
        
        # Buscar en la respuesta (menor peso)
        respuesta_item = re.sub(r'[¿?¡!.,;:]', '', item.answer.lower())
        palabras_respuesta = set(respuesta_item.split())
        coincidencias_respuesta = palabras_filtradas.intersection(palabras_respuesta)
        score += len(coincidencias_respuesta) * 0.1  # 10% por coincidencias en respuesta
        
        # Normalizar score por el total de palabras
        score_normalizado = score / total_palabras if total_palabras > 0 else 0
        
        if score_normalizado > mejor_score:
            mejor_score = score_normalizado
            mejor_match = item
    
    return mejor_match, mejor_score


def _buscar_fuzzy(pregunta: str) -> Tuple[Optional[ChatbotKnowledgeBase], float]:
    """
    Búsqueda fuzzy para manejar errores de tipeo y variaciones.
    """
    from difflib import SequenceMatcher
    
    # Normalizar pregunta
    pregunta_normalizada = pregunta.lower().strip()
    
    knowledge_items = ChatbotKnowledgeBase.objects.filter(is_active=True)
    
    mejor_match = None
    mejor_score = 0.0
    
    for item in knowledge_items:
        # Comparar con la pregunta almacenada
        similitud_pregunta = SequenceMatcher(None, pregunta_normalizada, item.question.lower()).ratio()
        
        # Comparar con keywords si existen
        similitud_keywords = 0.0
        if item.keywords:
            for keyword in item.keywords.split(','):
                keyword_limpio = keyword.strip().lower()
                sim_kw = SequenceMatcher(None, pregunta_normalizada, keyword_limpio).ratio()
                similitud_keywords = max(similitud_keywords, sim_kw)
        
        # Tomar la mejor similitud
        score_final = max(similitud_pregunta, similitud_keywords * 0.8)
        
        if score_final > mejor_score:
            mejor_score = score_final
            mejor_match = item
    
    return mejor_match, mejor_score


def _encontrar_mejor_coincidencia(pregunta: str) -> Tuple[Optional[ChatbotKnowledgeBase], float]:
    """
    Encuentra la mejor coincidencia para una pregunta usando IA.
    
    Returns:
        Tuple con el objeto ChatbotKnowledgeBase más similar y su score de similitud
    """
    if not _model_manager.is_available():
        raise ModelNotAvailableError("El modelo de IA no está disponible")
    
    # Obtener todas las preguntas con embeddings
    knowledge_items = ChatbotKnowledgeBase.objects.filter(
        is_active=True,
        question_embedding__isnull=False
    )
    
    if not knowledge_items.exists():
        raise NoKnowledgeBaseError("No hay elementos en la base de conocimiento con embeddings")
    
    # Generar embedding para la pregunta del usuario
    question_embedding = _model_manager.model.encode([pregunta])
    
    best_match = None
    best_score = 0.0
    
    for item in knowledge_items:
        if item.question_embedding:
            # Convertir embedding guardado a numpy array con el tipo correcto
            stored_embedding = np.array(item.question_embedding, dtype=np.float32).reshape(1, -1)
            
            # Asegurar que el question_embedding también sea float32
            question_embedding_float32 = question_embedding.astype(np.float32)
            
            # Calcular similitud coseno
            similarity = util.cos_sim(question_embedding_float32, stored_embedding).item()
            
            if similarity > best_score:
                best_score = similarity
                best_match = item
    
    return best_match, best_score


def procesar_consulta_con_ia(pregunta: str, user_id=None, session_id='anonymous', use_cache=True) -> Dict:
    """
    Procesa una consulta del chatbot usando IA para encontrar la mejor respuesta.
    
    Args:
        pregunta: La pregunta del usuario
        user_id: ID del usuario (opcional)
        session_id: ID de sesión
        use_cache: Si usar caché para respuestas
        
    Returns:
        Dict con la respuesta y metadatos
    """
    if len(pregunta.strip()) < 3:
        raise InvalidQuestionError("La pregunta es demasiado corta")
    
    # Verificar caché primero
    if use_cache:
        cached_response = _get_cached_response(pregunta)
        if cached_response:
            cached_response['cached'] = True
            return cached_response
    
    try:
        # SISTEMA DE BÚSQUEDA MULTI-NIVEL
        best_match = None
        similarity_score = 0.0
        search_method = "none"
        
        # NIVEL 1: Búsqueda por Embeddings/IA (más precisa)
        try:
            best_match, similarity_score = _encontrar_mejor_coincidencia(pregunta)
            if best_match and similarity_score >= SIMILARITY_THRESHOLD:
                search_method = "ai_embeddings"
                logger.info(f"Encontrado por IA: {similarity_score:.3f}")
        except (ModelNotAvailableError, NoKnowledgeBaseError) as e:
            logger.warning(f"Embeddings no disponibles: {e}")
        
        # NIVEL 2: Búsqueda por Keywords (si IA no encontró nada bueno)
        if not best_match or similarity_score < SIMILARITY_THRESHOLD:
            keyword_match, keyword_score = _buscar_por_keywords(pregunta)
            if keyword_match and keyword_score >= KEYWORD_MINIMUM_SCORE:
                # Si keyword es mejor que AI, usar keyword
                if keyword_score > similarity_score:
                    best_match = keyword_match
                    similarity_score = keyword_score
                    search_method = "keywords"
                    logger.info(f"Encontrado por keywords: {keyword_score:.3f}")
        
        # NIVEL 3: Búsqueda Fuzzy (si nada anterior funcionó)
        if not best_match or similarity_score < KEYWORD_MINIMUM_SCORE:
            fuzzy_match, fuzzy_score = _buscar_fuzzy(pregunta)
            if fuzzy_match and fuzzy_score > similarity_score:
                best_match = fuzzy_match
                similarity_score = fuzzy_score
                search_method = "fuzzy"
                logger.info(f"Encontrado por fuzzy: {fuzzy_score:.3f}")
        
        # Preparar respuesta
        response = {
            'answer': None,
            'match_question': None,
            'score': similarity_score,
            'search_method': search_method,
            'recommended_questions': [],
            'knowledge_id': None,
            'category': None,
            'cached': False
        }
        
        # Si encontramos una coincidencia válida
        if best_match and (
            (search_method == "ai_embeddings" and similarity_score >= SIMILARITY_THRESHOLD) or
            (search_method == "keywords" and similarity_score >= KEYWORD_MINIMUM_SCORE) or
            (search_method == "fuzzy" and similarity_score >= 0.6)  # Mayor threshold para fuzzy
        ):
            # Respuesta encontrada
            response.update({
                'answer': best_match.answer,
                'match_question': best_match.question,
                'knowledge_id': best_match.id,
                'category': best_match.category.name if best_match.category else None
            })
            
            # Incrementar contador de vistas
            best_match.view_count += 1
            best_match.save(update_fields=['view_count'])
            
            # Obtener preguntas recomendadas
            recommended = best_match.recommended_questions.filter(is_active=True)[:3]
            response['recommended_questions'] = [
                {
                    'id': q.id,
                    'question': q.question,
                    'category': q.category.name if q.category else None
                }
                for q in recommended
            ]
            
        else:
            # No se encontró una buena coincidencia
            response['answer'] = "Lo siento, no tengo información específica sobre eso. ¿Podrías reformular tu pregunta o ser más específico?"
            
            # Obtener preguntas frecuentes como alternativa
            frequent_questions = ChatbotKnowledgeBase.objects.filter(
                is_active=True
            ).order_by('-view_count')[:3]
            
            response['recommended_questions'] = [
                {
                    'id': q.id,
                    'question': q.question,
                    'category': q.category.name if q.category else None
                }
                for q in frequent_questions
            ]
        
        # Registrar conversación si hay usuario
        if user_id:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(id=user_id)
                
                ChatConversation.objects.create(
                    user=user,
                    session_id=session_id,
                    question_text=pregunta,
                    answer_text=response['answer'],
                    matched_knowledge=best_match
                )
            except Exception as e:
                logger.warning(f"Error al registrar conversación: {e}")
        
        # Guardar en caché
        if use_cache and response['answer']:
            _set_cached_response(pregunta, response)
        
        return response
        
    except (ModelNotAvailableError, NoKnowledgeBaseError) as e:
        logger.error(f"Error en procesamiento de consulta: {e}")
        return {
            'answer': 'El servicio de chatbot no está disponible temporalmente. Por favor, intenta más tarde.',
            'match_question': None,
            'score': 0,
            'recommended_questions': [],
            'knowledge_id': None,
            'category': None,
            'cached': False,
            'error': str(e)
        }