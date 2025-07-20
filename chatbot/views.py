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
from drf_spectacular.utils import extend_schema
from core.viewsets import AuditModelViewSet

# Lista de palabras comunes en español a ignorar durante la búsqueda
SPANISH_STOP_WORDS = [
    'de', 'la', 'el', 'en', 'y', 'a', 'los', 'del', 'las', 'un', 'por', 'con', 'no',
    'una', 'su', 'para', 'es', 'al', 'lo', 'como', 'más', 'o', 'pero', 'sus', 'le',
    'ha', 'me', 'si', 'sin', 'sobre', 'este', 'ya', 'entre', 'cuando', 'muy',
    'también', 'hasta', 'desde', 'mi', 'qué', 'dónde', 'quién', 'cuál', 'cómo', 'cuándo'
]

# Create your views here.

@extend_schema(tags=['Chatbot'])
class ChatbotKnowledgeBaseViewSet(AuditModelViewSet):
    """
    API endpoint para la gestión de la base de conocimiento del Chatbot.
    Accesible solo por el rol Admin.
    """
    queryset = ChatbotKnowledgeBase.objects.all().select_related('category', 'created_by', 'updated_by')
    serializer_class = ChatbotKnowledgeBaseSerializer
    
    def get_permissions(self):
        """
        Solo los usuarios en el grupo 'Admin' tienen acceso a este recurso.
        """
        return [permissions.IsAuthenticated(), IsInGroup('Admin')]

    # Para este ViewSet, todas las acciones (GET, POST, PUT, DELETE)
    # requieren los mismos permisos, por lo que no es necesario
    # un método get_permissions() como en Eventos.


@extend_schema(tags=['Chatbot'])
class ChatConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint para ver el historial de conversaciones del chatbot.
    Accesible solo para el rol 'Admin'.
    Permite a los administradores revisar las preguntas de los usuarios
    para mejorar la base de conocimiento.
    """
    queryset = ChatConversation.objects.all().select_related('user', 'matched_knowledge', 'created_by', 'updated_by')
    serializer_class = ChatConversationSerializer
    permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin')]

    def get_permissions(self):
        """
        Instancia y devuelve la lista de permisos que esta vista requiere.
        Necesario porque IsInGroup se instancia con parámetros.
        """
        return [permission() if hasattr(permission, '__call__') else permission for permission in self.permission_classes]

    def get_queryset(self):
        """
        Sobrescribe el queryset para optimizar las consultas y
        asegurar que se incluyan los datos relacionados.
        """
        return super().get_queryset().order_by('-created_at')


@extend_schema(tags=['Chatbot'])
class ChatbotQueryView(APIView):
    """
    Endpoint público para hacer preguntas al chatbot.
    Recibe una pregunta y devuelve una respuesta de la base de conocimiento.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=QuestionSerializer,
        responses={200: AnswerSerializer}
    )
    def post(self, request, *args, **kwargs):
        serializer = QuestionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        question_text = serializer.validated_data['question'].strip().lower()
        session_id = serializer.validated_data.get('session_id') # .get() para no fallar si no viene
        
        # Si no hay session_id, se crea uno para el seguimiento anónimo
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        answer_text = "Lo siento, no he podido encontrar una respuesta a tu pregunta. Por favor, intenta reformularla."
        matched_knowledge = None

        # 1. Limpiar la pregunta, obtener términos y filtrar "stop words"
        raw_terms = ''.join(c for c in question_text if c.isalnum() or c.isspace()).split()
        search_terms = [term for term in raw_terms if term not in SPANISH_STOP_WORDS]

        if search_terms:
            # 2. Encontrar candidatos iniciales en la base de datos
            query = reduce(operator.or_, (Q(question__icontains=term) | Q(keywords__icontains=term) for term in search_terms))
            candidate_entries = ChatbotKnowledgeBase.objects.filter(is_active=True).filter(query).distinct()

            # 3. Calcular el score para cada candidato y encontrar el mejor
            best_match = None
            highest_score = 0

            if candidate_entries.exists():
                for entry in candidate_entries:
                    current_score = 0
                    entry_question_lower = entry.question.lower()
                    entry_keywords_lower = entry.keywords.lower()

                    for term in search_terms:
                        if term in entry_question_lower:
                            current_score += 3  # Mayor peso
                        if term in entry_keywords_lower:
                            current_score += 1  # Menor peso

                    if current_score > highest_score:
                        highest_score = current_score
                        best_match = entry
                
                if best_match:
                    answer_text = best_match.answer
                    matched_knowledge = best_match

        # Registrar la conversación, incluyendo auditoría si el usuario está autenticado
        user = request.user if request.user.is_authenticated else None
        
        conversation_data = {
            'session_id': session_id,
            'question_text': question_text,
            'answer_text': answer_text,
            'matched_knowledge': matched_knowledge,
            'user': user
        }

        if user:
            conversation_data['created_by'] = user
            conversation_data['updated_by'] = user

        ChatConversation.objects.create(**conversation_data)

        answer_serializer = AnswerSerializer({'answer': answer_text, 'session_id': session_id})
        return Response(answer_serializer.data, status=status.HTTP_200_OK)
