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

from .models import ChatbotKnowledgeBase, ChatConversation, ChatbotCategory
from .serializers import (
    ChatbotQuerySerializer,
    ChatbotKnowledgeBaseSerializer,
    ChatConversationSerializer,
    ChatbotCategorySerializer
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
            # Temporalmente permitir acceso a cualquier usuario autenticado
            permission_classes = [permissions.IsAuthenticated]
        return [permission() if isinstance(permission, type) else permission for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        try:
            response = super().list(request, *args, **kwargs)
            return Response({
                "status": "success",
                "data": response.data
            })
        except Exception as e:
            logger.error(f"Error al listar base de conocimiento: {e}")
            return Response({
                "status": "error",
                "error": {
                    "code": "server_error",
                    "message": "Error interno del servidor"
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            return Response({
                "status": "success",
                "data": response.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error al crear entrada: {e}")
            return Response({
                "status": "error",
                "error": {
                    "code": "server_error",
                    "message": "Error interno del servidor"
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

    @extend_schema(
        summary="Importación Masiva de Conocimientos",
        description="Permite importar múltiples entradas de base de conocimiento desde un archivo JSON"
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsInGroup('Admin', 'QA')])
    def bulk_import(self, request):
        try:
            if 'file' not in request.FILES:
                return Response({"status": "error", "error": "No se proporcionó ningún archivo"}, status=status.HTTP_400_BAD_REQUEST)
            
            file = request.FILES['file']
            if not file.name.endswith('.json'):
                return Response({"status": "error", "error": "El archivo debe ser un JSON válido"}, status=status.HTTP_400_BAD_REQUEST)
            
            import json
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                return Response({"status": "error", "error": "El archivo JSON no es válido"}, status=status.HTTP_400_BAD_REQUEST)
            
            if not isinstance(data, list):
                return Response({"status": "error", "error": "El JSON debe contener una lista de objetos"}, status=status.HTTP_400_BAD_REQUEST)
            
            imported_count = 0
            errors = []
            
            for item in data:
                try:
                    serializer = ChatbotKnowledgeBaseSerializer(data=item, context={'request': request})
                    if serializer.is_valid():
                        serializer.save(created_by=request.user, updated_by=request.user)
                        imported_count += 1
                    else:
                        errors.append(f"Error en elemento: {serializer.errors}")
                except Exception as e:
                    errors.append(f"Error procesando elemento: {str(e)}")
            
            return Response({
                "status": "success", 
                "data": {
                    "imported": imported_count,
                    "total": len(data),
                    "errors": errors[:10] if errors else []  # Limitar errores mostrados
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error en importación masiva: {e}")
            return Response({"status": "error", "error": "Error interno en importación masiva"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        summary="Regenerar Embeddings",
        description="Regenera los embeddings de todas las entradas de la base de conocimiento"
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsInGroup('Admin', 'QA')])
    def regenerate_embeddings(self, request):
        try:
            from django.core.management import call_command
            from io import StringIO
            
            # Capturar la salida del comando
            out = StringIO()
            
            # Ejecutar el comando de generación de embeddings
            call_command('generate_embeddings', stdout=out)
            
            # Contar cuántas entradas fueron actualizadas
            updated_count = ChatbotKnowledgeBase.objects.exclude(question_embedding__isnull=True).count()
            
            return Response({
                "status": "success", 
                "data": {
                    "message": "Embeddings regenerados exitosamente",
                    "updated_count": updated_count,
                    "details": out.getvalue()
                }
            })
            
        except Exception as e:
            logger.error(f"Error al regenerar embeddings: {e}")
            return Response({
                "status": "error", 
                "error": f"Error al regenerar embeddings: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=['Conversations'])
class ChatConversationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChatConversation.objects.all()
    serializer_class = ChatConversationSerializer
    
    def get_permissions(self):
        """
        Configurar permisos para el viewset de conversaciones
        """
        permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin', 'QA')]
        return [permission() if isinstance(permission, type) else permission for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        try:
            response = super().list(request, *args, **kwargs)
            return response
        except Exception as e:
            logger.error(f"Error al listar conversaciones: {e}")
            return Response({"status": "error", "error": "Error interno del servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        try:
            response = super().retrieve(request, *args, **kwargs)
            return Response({"status": "success", "data": response.data})
        except Exception as e:
            logger.error(f"Error al obtener conversación: {e}")
            return Response({"status": "error", "error": "Error interno del servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=['Chatbot Categories'])
class ChatbotCategoryViewSet(viewsets.ModelViewSet):
    queryset = ChatbotCategory.objects.all()
    serializer_class = ChatbotCategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin', 'QA')]

    def get_permissions(self):
        """Sobrescribir get_permissions para instanciar correctamente IsInGroup."""
        permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin', 'QA')]
        return [permission() if isinstance(permission, type) else permission for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        try:
            response = super().list(request, *args, **kwargs)
            return Response({
                "status": "success", 
                "data": response.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error al listar categorías: {e}")
            return Response({"status": "error", "error": "Error interno del servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            return Response({"status": "success", "data": response.data}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error al crear categoría: {e}")
            return Response({"status": "error", "error": "Error al crear la categoría"}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        try:
            response = super().retrieve(request, *args, **kwargs)
            return Response({"status": "success", "data": response.data})
        except Exception as e:
            logger.error(f"Error al obtener categoría: {e}")
            return Response({"status": "error", "error": "Categoría no encontrada"}, status=status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        try:
            response = super().update(request, *args, **kwargs)
            return Response({"status": "success", "data": response.data})
        except Exception as e:
            logger.error(f"Error al actualizar categoría: {e}")
            return Response({"status": "error", "error": "Error al actualizar la categoría"}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            super().destroy(request, *args, **kwargs)
            return Response({"status": "success", "data": {"message": "Categoría eliminada exitosamente"}}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error al eliminar categoría: {e}")
            return Response({"status": "error", "error": "Error al eliminar la categoría"}, status=status.HTTP_400_BAD_REQUEST)


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