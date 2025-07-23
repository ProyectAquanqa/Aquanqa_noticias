# type: ignore

from django.shortcuts import render
from rest_framework import viewsets, permissions
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ChatbotKnowledgeBase, ChatConversation
from .serializers import (
    ChatbotKnowledgeBaseSerializer, QuestionSerializer, 
    AnswerSerializer, ChatConversationSerializer, RecommendedQuestionSerializer
)
from core.permissions import IsInGroup
from functools import reduce
import operator
import uuid
from drf_spectacular.utils import extend_schema
from core.viewsets import AuditModelViewSet
from thefuzz import process

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
    en la base de conocimiento utilizando búsqueda flexible (fuzzy matching).
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=QuestionSerializer,
        responses={200: AnswerSerializer}
    )
    def post(self, request, *args, **kwargs):
        """
        Procesa una pregunta del usuario y retorna una respuesta.
        """
        serializer = QuestionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        question_text = validated_data['question'].strip().lower()
        session_id = validated_data.get('session_id') or str(uuid.uuid4())
        
        answer_text = "Lo siento, no he podido encontrar una respuesta a tu pregunta. Por favor, intenta reformularla."
        matched_knowledge = None

        # 1. Obtener todas las preguntas activas de la base de conocimiento.
        #    Se usa un diccionario para mapear el texto de la pregunta a su ID para una búsqueda eficiente.
        active_questions = {
            entry.question: entry.id 
            for entry in ChatbotKnowledgeBase.objects.filter(is_active=True)
        }

        if active_questions:
            # 2. Utilizar thefuzz para encontrar la mejor coincidencia.
            #    `extractOne` devuelve la mejor coincidencia que supera el `score_cutoff`.
            #    El formato de la tupla es: (texto_pregunta, puntuacion, clave_del_diccionario)
            #    En nuestro caso, la clave es la misma que el texto.
            best_match = process.extractOne(question_text, active_questions.keys(), score_cutoff=80)

            if best_match:
                # 3. Si se encuentra una coincidencia, obtener la entrada completa de la base de datos.
                question_found = best_match[0]
                knowledge_id = active_questions[question_found]
                
                best_entry = ChatbotKnowledgeBase.objects.get(id=knowledge_id)
                answer_text = best_entry.answer
                matched_knowledge = best_entry

        # 4. Registrar la conversación para auditoría.
        self._log_conversation(request, session_id, question_text, answer_text, matched_knowledge)

        answer_serializer = AnswerSerializer({'answer': answer_text, 'session_id': session_id})
        return Response(answer_serializer.data, status=status.HTTP_200_OK)

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

@extend_schema(tags=['Chatbot'])
class RecommendedQuestionsView(APIView):
    """
    Endpoint público que devuelve una lista de preguntas recomendadas.

    Estas son preguntas predefinidas que se pueden mostrar al usuario
    para guiar la conversación.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        responses={200: RecommendedQuestionSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        """
        Retorna las preguntas marcadas como 'recomendadas' en la base de conocimiento.
        """
        recommended_questions = ChatbotKnowledgeBase.objects.filter(
            is_active=True, 
            is_recommended=True
        ).order_by('?')[:5]  # Devuelve hasta 5 preguntas aleatorias

        serializer = RecommendedQuestionSerializer(recommended_questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
