# type: ignore

from django.shortcuts import render
from rest_framework import viewsets, permissions
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ChatbotKnowledgeBase, ChatConversation
from .serializers import ChatbotKnowledgeBaseSerializer, QuestionSerializer, AnswerSerializer, ChatConversationSerializer
from core.permissions import IsInGroup
from functools import reduce
import operator
import uuid
from drf_spectacular.utils import extend_schema
from core.viewsets import AuditModelViewSet

# Lista de palabras comunes en español a ignorar para no ensuciar la búsqueda.
SPANISH_STOP_WORDS = [
    'de', 'la', 'el', 'en', 'y', 'a', 'los', 'del', 'las', 'un', 'por', 'con', 'no',
    'una', 'su', 'para', 'es', 'al', 'lo', 'como', 'más', 'o', 'pero', 'sus', 'le',
    'ha', 'me', 'si', 'sin', 'sobre', 'este', 'ya', 'entre', 'cuando', 'muy',
    'también', 'hasta', 'desde', 'mi', 'qué', 'dónde', 'quién', 'cuál', 'cómo', 'cuándo'
]

@extend_schema(tags=['Chatbot'])
class ChatbotKnowledgeBaseViewSet(AuditModelViewSet):
    """
    Gestiona la base de conocimiento del chatbot (CRUD).
    
    Accesible solo por administradores para crear, leer, actualizar y eliminar
    entradas de conocimiento.
    """
    queryset = ChatbotKnowledgeBase.objects.all().select_related('category', 'created_by', 'updated_by')
    serializer_class = ChatbotKnowledgeBaseSerializer
    permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin')]

@extend_schema(tags=['Chatbot'])
class ChatConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Expone el historial de conversaciones del chatbot (solo lectura).

    Permite a los administradores revisar las interacciones para mejorar la
    efectividad del chatbot.
    """
    queryset = ChatConversation.objects.all().select_related('user', 'matched_knowledge').order_by('-created_at')
    serializer_class = ChatConversationSerializer
    permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin')]

@extend_schema(tags=['Chatbot'])
class ChatbotQueryView(APIView):
    """
    Endpoint público para interactuar con el chatbot.

    Recibe una pregunta y devuelve la respuesta más relevante que encuentre
    en la base de conocimiento.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=QuestionSerializer,
        responses={200: AnswerSerializer}
    )
    def post(self, request, *args, **kwargs):
        """
        Procesa una pregunta del usuario y retorna una respuesta.

        Args:
            request: La petición HTTP, que debe contener 'question' y opcionalmente 'session_id'.
        
        Returns:
            Response: Un objeto JSON con la 'answer' y el 'session_id' de la conversación.
        """
        serializer = QuestionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        question_text = validated_data['question'].strip().lower()
        session_id = validated_data.get('session_id') or str(uuid.uuid4())
        
        answer_text = "Lo siento, no he podido encontrar una respuesta a tu pregunta. Por favor, intenta reformularla."
        matched_knowledge = None

        # 1. Limpiar y tokenizar la pregunta, excluyendo palabras comunes (stop words).
        raw_terms = ''.join(c for c in question_text if c.isalnum() or c.isspace()).split()
        search_terms = [term for term in raw_terms if term not in SPANISH_STOP_WORDS]

        if search_terms:
            # 2. Construir una consulta para buscar términos en preguntas o palabras clave.
            query = reduce(operator.or_, (Q(question__icontains=term) | Q(keywords__icontains=term) for term in search_terms))
            candidate_entries = ChatbotKnowledgeBase.objects.filter(is_active=True).filter(query).distinct()

            # 3. Puntuar cada candidato para encontrar la mejor coincidencia.
            #    Se da más peso a las coincidencias en la pregunta que en las palabras clave.
            best_match = None
            highest_score = 0

            if candidate_entries.exists():
                for entry in candidate_entries:
                    score = self._calculate_score(entry, search_terms)
                    if score > highest_score:
                        highest_score = score
                        best_match = entry
                
                if best_match:
                    answer_text = best_match.answer
                    matched_knowledge = best_match

        # 4. Registrar la conversación para auditoría.
        self._log_conversation(request, session_id, question_text, answer_text, matched_knowledge)

        answer_serializer = AnswerSerializer({'answer': answer_text, 'session_id': session_id})
        return Response(answer_serializer.data, status=status.HTTP_200_OK)

    def _calculate_score(self, entry, search_terms):
        """
        Calcula una puntuación de relevancia para una entrada de conocimiento.
        
        Args:
            entry (ChatbotKnowledgeBase): La entrada a puntuar.
            search_terms (list): Lista de términos de búsqueda.
        
        Returns:
            int: La puntuación calculada.
        """
        score = 0
        entry_question = entry.question.lower()
        entry_keywords = entry.keywords.lower()

        for term in search_terms:
            if term in entry_question:
                score += 3  # Mayor peso para coincidencias en la pregunta.
            if term in entry_keywords:
                score += 1  # Menor peso para coincidencias en keywords.
        return score

    def _log_conversation(self, request, session_id, question, answer, matched_knowledge):
        """
        Guarda un registro de la interacción en la base de datos.
        """
        user = request.user if request.user.is_authenticated else None
        
        log_data = {
            'session_id': session_id,
            'question_text': question,
            'answer_text': answer,
            'matched_knowledge': matched_knowledge,
            'user': user
        }

        if user:
            log_data['created_by'] = user
            log_data['updated_by'] = user

        ChatConversation.objects.create(**log_data)
