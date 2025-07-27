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
SIMILARITY_THRESHOLD = 0.6
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
        # Buscar la mejor coincidencia usando IA
        best_match, similarity_score = _encontrar_mejor_coincidencia(pregunta)
        
        response = {
            'answer': None,
            'match_question': None,
            'score': similarity_score,
            'recommended_questions': [],
            'knowledge_id': None,
            'category': None,
            'cached': False
        }
        
        if best_match and similarity_score >= SIMILARITY_THRESHOLD:
            # Respuesta encontrada con confianza suficiente
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