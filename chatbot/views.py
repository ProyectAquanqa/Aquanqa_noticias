# type: ignore

from django.shortcuts import render
from rest_framework import viewsets, permissions
from django.db.models import Q, F, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ChatbotKnowledgeBase, ChatConversation
from .serializers import (
    ChatbotQuerySerializer,
    ChatbotKnowledgeBaseSerializer,
    RecommendedQuestionSerializer,
    ChatConversationSerializer
)
from core.permissions import IsInGroup
from core.viewsets import AuditModelViewSet
from sentence_transformers import SentenceTransformer, util
import torch
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

# --- Carga del Modelo de IA ---
# Se carga el modelo una sola vez cuando el servidor Django se inicia.
# Esto es mucho más eficiente que cargarlo en cada petición.
# Usamos el mismo modelo que en el comando de generación para asegurar consistencia.
MODEL_NAME = 'hiiamsid/sentence_similarity_spanish_es'
try:
    # Determinar el dispositivo a usar (GPU si está disponible, si no CPU)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Chatbot: Cargando modelo '{MODEL_NAME}' en el dispositivo: {device}")
    model = SentenceTransformer(MODEL_NAME, device=device)
    print("Chatbot: Modelo cargado exitosamente.")
except Exception as e:
    print(f"Error crítico: No se pudo cargar el modelo de SentenceTransformer. {e}")
    model = None

@extend_schema(tags=['Knowledge'])
class ChatbotKnowledgeBaseViewSet(AuditModelViewSet):
    """
    Gestiona la base de conocimiento del chatbot (CRUD).
    
    Accesible solo por administradores para crear, leer, actualizar y eliminar
    entradas de conocimiento.
    """
    queryset = ChatbotKnowledgeBase.objects.all().select_related('category', 'created_by', 'updated_by')
    serializer_class = ChatbotKnowledgeBaseSerializer
    
    def get_permissions(self):
        """Devuelve una lista de instancias de los permisos requeridos."""
        return [permissions.IsAuthenticated(), IsInGroup('Admin')]

    @extend_schema(summary="Listar Base de Conocimiento (Admin)")
    def list(self, request, *args, **kwargs):
        """Obtiene una lista de todas las entradas de la base de conocimiento."""
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Crear Entrada de Conocimiento (Admin)")
    def create(self, request, *args, **kwargs):
        """Crea una nueva entrada de pregunta-respuesta en la base de conocimiento."""
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Obtener Entrada de Conocimiento (Admin)")
    def retrieve(self, request, *args, **kwargs):
        """Obtiene una entrada específica de la base de conocimiento por su ID."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Actualizar Entrada de Conocimiento (Admin)")
    def update(self, request, *args, **kwargs):
        """Actualiza completamente una entrada de la base de conocimiento."""
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Actualización Parcial de Conocimiento (Admin)")
    def partial_update(self, request, *args, **kwargs):
        """Actualiza parcialmente una entrada de la base de conocimiento."""
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Eliminar Entrada de Conocimiento (Admin)")
    def destroy(self, request, *args, **kwargs):
        """Elimina una entrada de la base de conocimiento."""
        return super().destroy(request, *args, **kwargs)

@extend_schema(tags=['Chat History'])
class ChatConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Expone el historial de conversaciones del chatbot (solo lectura).

    Permite a los administradores revisar las interacciones para mejorar la
    efectividad del chatbot.
    """
    queryset = ChatConversation.objects.all().select_related('user', 'matched_knowledge').order_by('-created_at')
    serializer_class = ChatConversationSerializer

    def get_permissions(self):
        """Devuelve una lista de instancias de los permisos requeridos."""
        return [permissions.IsAuthenticated(), IsInGroup('Admin')]

    @extend_schema(summary="Listar Historial de Conversaciones (Admin)")
    def list(self, request, *args, **kwargs):
        """Obtiene el historial completo de conversaciones del chatbot."""
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Obtener una Conversación (Admin)")
    def retrieve(self, request, *args, **kwargs):
        """Obtiene una conversación específica del historial por su ID."""
        return super().retrieve(request, *args, **kwargs)

class ChatbotQueryView(APIView):
    """
    Gestiona las consultas del chatbot de los usuarios. Utiliza búsqueda por similitud
    semántica para encontrar la respuesta más relevante en la base de conocimientos.
    """
    permission_classes = [AllowAny]
    # Umbral de similitud: Si la mejor coincidencia no supera este valor,
    # se considera que no se encontró una respuesta adecuada.
    # Se puede ajustar según la sensibilidad deseada.
    # se puede bajar a 0.4 para asegurar que las coincidencias de palabras clave simples funcionen.
    SIMILARITY_THRESHOLD = 0.6

    def post(self, request, *args, **kwargs):
        if not model:
            return Response({
                "error": "El servicio de Chatbot no está disponible temporalmente debido a un problema con el modelo de IA."
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        serializer = ChatbotQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_question = serializer.validated_data['question']

        # 1. Obtener todos los conocimientos activos con embeddings pre-calculados.
        #    Se excluyen los que no tienen un embedding para evitar errores.
        knowledge_base = ChatbotKnowledgeBase.objects.filter(is_active=True, question_embedding__isnull=False)
        if not knowledge_base.exists():
            return self.default_response()

        # 2. Preparar los datos para la comparación.
        #    - db_questions: lista de los textos de las preguntas.
        #    - db_embeddings: tensor de PyTorch con todos los embeddings de la DB.
        db_questions = [item.question for item in knowledge_base]
        db_embeddings = torch.tensor([item.question_embedding for item in knowledge_base], device=model.device)

        # 3. Codificar la pregunta del usuario en un vector (embedding).
        user_embedding = model.encode(user_question, convert_to_tensor=True, device=model.device)

        # 4. Calcular la similitud del coseno entre la pregunta del usuario y TODAS las de la BD.
        #    Esto es extremadamente rápido gracias a las operaciones vectoriales.
        cosine_scores = util.cos_sim(user_embedding, db_embeddings)

        # 5. Encontrar la puntuación más alta y su índice.
        best_match_score, best_match_idx = torch.max(cosine_scores, dim=1)
        best_match_score = best_match_score.item()
        best_match_idx = best_match_idx.item()
        
        # --- LOGS DE DEPURACIÓN ---
        print("-" * 30)
        print(f"Pregunta del usuario: '{user_question}'")
        print(f"Se comparó con {len(db_questions)} preguntas de la base de datos.")
        print(f"Mejor coincidencia encontrada: '{db_questions[best_match_idx]}'")
        print(f"Puntuación de similitud: {best_match_score:.4f}")
        print(f"Umbral requerido: {self.SIMILARITY_THRESHOLD}")
        print("-" * 30)
        # --- FIN DE LOGS DE DEPURACIÓN ---

        # 6. Evaluar si la mejor coincidencia es suficientemente buena.
        if best_match_score >= self.SIMILARITY_THRESHOLD:
            best_match = knowledge_base[best_match_idx]
            # Incrementar el contador de vistas de la pregunta encontrada
            best_match.view_count += 1
            best_match.save(update_fields=['view_count'])

            # Serializar las preguntas recomendadas si existen
            recommended = RecommendedQuestionSerializer(best_match.recommended_questions.all(), many=True).data

            response_data = {
                'answer': best_match.answer,
                'match_question': best_match.question,
                'score': best_match_score,
                'recommended_questions': recommended
            }

            self.log_conversation(request, user_question, best_match.answer, best_match)

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            # Si no se encuentra una coincidencia clara, dar una respuesta por defecto
            # y sugerir las preguntas más frecuentes.
            response = self.default_response()
            self.log_conversation(request, user_question, response.data['answer'], None)
            return response

    def default_response(self):
        """
        Retorna una respuesta estándar y las preguntas más frecuentes cuando
        no se encuentra una coincidencia adecuada.
        """
        # Obtener las 4 preguntas más vistas para usarlas como sugerencias generales
        frequent_questions = ChatbotKnowledgeBase.objects.filter(is_active=True).order_by('-view_count')[:4]
        suggestions = RecommendedQuestionSerializer(frequent_questions, many=True).data

        return Response({
            'answer': 'Lo siento, no he podido encontrar una respuesta a tu pregunta. Quizás una de estas te ayude:',
            'match_question': None,
            'score': 0,
            'recommended_questions': suggestions
        }, status=status.HTTP_200_OK)

    def log_conversation(self, request, question_text, answer_text, matched_knowledge):
        """
        Guarda un registro de la interacción en el historial de conversaciones.
        """
        user = request.user if request.user.is_authenticated else None
        session_id = request.session.session_key or 'anonymous'
        
        ChatConversation.objects.create(
            session_id=session_id,
            user=user,
            question_text=question_text,
            answer_text=answer_text,
            matched_knowledge=matched_knowledge
        )

@extend_schema(
    tags=['Chatbot'],
    summary="Obtener Preguntas Frecuentes",
    description="Devuelve una lista de las 5 preguntas más populares para mostrar al iniciar el chat."
)
class FrequentQuestionsView(APIView):
    """
    Endpoint público que devuelve una lista de las preguntas más frecuentes.

    Se basa en un contador de vistas para determinar la popularidad.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        responses={200: RecommendedQuestionSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        """
        Retorna las 5 preguntas más vistas de la base de conocimiento.
        """
        frequent_questions = ChatbotKnowledgeBase.objects.filter(is_active=True).order_by('-view_count')[:5]
        serializer = RecommendedQuestionSerializer(frequent_questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
