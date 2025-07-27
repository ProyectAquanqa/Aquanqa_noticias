"""
Vistas del módulo chatbot.
"""

import logging
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.utils import timezone

from .models import ChatbotKnowledgeBase, ChatConversation
from .serializers import (
    ChatbotQuerySerializer,
    ChatbotKnowledgeBaseSerializer,
    ChatConversationSerializer
)
from .services import (
    procesar_consulta_chatbot,
    obtener_preguntas_frecuentes,
    obtener_estadisticas_chatbot,
    ModelNotAvailableError,
    NoKnowledgeBaseError,
    InvalidQuestionError,
    ChatbotServiceError,
    RateLimitError
)
from core.permissions import IsInGroup
from core.viewsets import AuditModelViewSet

logger = logging.getLogger(__name__)


@extend_schema(tags=['Knowledge Management'])
class ChatbotKnowledgeBaseViewSet(AuditModelViewSet):
    queryset = ChatbotKnowledgeBase.objects.all().select_related('category', 'created_by', 'updated_by')
    serializer_class = ChatbotKnowledgeBaseSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin', 'QA')]
        else:
            permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin', 'QA', 'Trabajador')]
        return [permission() if isinstance(permission, type) else permission for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        try:
            response = super().list(request, *args, **kwargs)
            return Response({"status": "success", "data": response.data})
        except Exception as e:
            logger.error(f"Error al listar base de conocimiento: {e}")
            return Response({"status": "error", "error": "Error interno del servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            return Response({"status": "success", "data": response.data}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error al crear entrada: {e}")
            return Response({"status": "error", "error": "Error al crear la entrada"}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        try:
            response = super().retrieve(request, *args, **kwargs)
            return Response({"status": "success", "data": response.data})
        except Exception as e:
            logger.error(f"Error al obtener entrada: {e}")
            return Response({"status": "error", "error": "Entrada no encontrada"}, status=status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        try:
            response = super().update(request, *args, **kwargs)
            return Response({"status": "success", "data": response.data})
        except Exception as e:
            logger.error(f"Error al actualizar entrada: {e}")
            return Response({"status": "error", "error": "Error al actualizar la entrada"}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        try:
            response = super().partial_update(request, *args, **kwargs)
            return Response({"status": "success", "data": response.data})
        except Exception as e:
            logger.error(f"Error al actualizar entrada: {e}")
            return Response({"status": "error", "error": "Error al actualizar la entrada"}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            super().destroy(request, *args, **kwargs)
            return Response({"status": "success", "data": {"message": "Entrada eliminada exitosamente"}}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error al eliminar entrada: {e}")
            return Response({"status": "error", "error": "Error al eliminar la entrada"}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Obtener Preguntas Frecuentes",
        parameters=[OpenApiParameter(name='limit', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Número máximo de preguntas (default: 10)')]
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def frequent_questions(self, request):
        try:
            limit = int(request.query_params.get('limit', 10))
            limit = min(limit, 50)
            preguntas = obtener_preguntas_frecuentes(limite=limit)
            return Response({"status": "success", "data": {"frequent_questions": preguntas, "total": len(preguntas)}})
        except Exception as e:
            logger.error(f"Error al obtener preguntas frecuentes: {e}")
            return Response({"status": "error", "error": "Error al obtener preguntas frecuentes"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsInGroup('Admin', 'QA')])
    def statistics(self, request):
        try:
            stats = obtener_estadisticas_chatbot()
            return Response({"status": "success", "data": stats})
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            return Response({"status": "error", "error": "Error al obtener estadísticas"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=['Conversations'])
class ChatConversationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChatConversation.objects.all().select_related('user', 'matched_knowledge')
    serializer_class = ChatConversationSerializer
    permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin', 'QA')]

    def list(self, request, *args, **kwargs):
        try:
            response = super().list(request, *args, **kwargs)
            return Response({"status": "success", "data": response.data})
        except Exception as e:
            logger.error(f"Error al listar conversaciones: {e}")
            return Response({"status": "error", "error": "Error interno del servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        try:
            response = super().retrieve(request, *args, **kwargs)
            return Response({"status": "success", "data": response.data})
        except Exception as e:
            logger.error(f"Error al obtener conversación: {e}")
            return Response({"status": "error", "error": "Conversación no encontrada"}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(tags=['Chatbot Query'])
class ChatbotQueryView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="Consultar Chatbot", request=ChatbotQuerySerializer)
    def post(self, request):
        try:
            serializer = ChatbotQuerySerializer(data=request.data)
            if not serializer.is_valid():
                return Response({"status": "error", "error": "Datos inválidos", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            pregunta = serializer.validated_data['question']
            session_id = serializer.validated_data.get('session_id', 'anonymous')
            use_cache = serializer.validated_data.get('use_cache', True)
            user_id = request.user.id if request.user.is_authenticated else None
            
            resultado = procesar_consulta_chatbot(
                pregunta=pregunta,
                user_id=user_id,
                session_id=session_id,
                use_cache=use_cache
            )
            
            resultado['cached'] = 'knowledge_id' in resultado and use_cache
            resultado['timestamp'] = timezone.now().isoformat()
            
            logger.info(f"Consulta procesada: {pregunta[:50]}... | Score: {resultado.get('score', 0)}")
            
            return Response({"status": "success", "data": resultado})

        except InvalidQuestionError as e:
            return Response({"status": "error", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ModelNotAvailableError as e:
            return Response({"status": "error", "error": "Servicio no disponible temporalmente"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except NoKnowledgeBaseError as e:
            return Response({"status": "error", "error": "Base de conocimiento no disponible"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except RateLimitError as e:
            return Response({"status": "error", "error": "Límite de consultas excedido"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except ChatbotServiceError as e:
            return Response({"status": "error", "error": "Error interno del chatbot"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            return Response({"status": "error", "error": "Error interno del servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=['Chatbot Query'])
class ChatbotRecommendedQuestionsView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Obtener Preguntas Recomendadas",
        parameters=[OpenApiParameter(name='limit', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Número máximo de preguntas (default: 5, max: 20)')]
    )
    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 5))
            limit = min(max(limit, 1), 20)
            preguntas = obtener_preguntas_frecuentes(limite=limit)
            return Response({"status": "success", "data": {"recommended_questions": preguntas, "total": len(preguntas)}})
        except Exception as e:
            logger.error(f"Error al obtener preguntas recomendadas: {e}")
            return Response({"status": "error", "error": "Error al obtener preguntas recomendadas"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 