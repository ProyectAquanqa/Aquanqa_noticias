"""
API URL Configuration for AquanQ Noticias.

Este módulo define las rutas de la API REST del proyecto AquanQ Noticias.
Incluye endpoints para:
- Gestión de eventos
- Sistema de chatbot y base de conocimiento
- Gestión de dispositivos y notificaciones
- Autenticación y gestión de usuarios

Todas las rutas definidas aquí están prefijadas con 'api/' en la configuración principal de URLs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from users.views import (
    UserRegistrationView, 
    UserProfileView,
    CustomTokenObtainPairView
)
from eventos.views import EventoViewSet, CategoriaViewSet
from chatbot.views import (
    ChatbotQueryView, 
    ChatbotRecommendedQuestionsView,
    ChatbotKnowledgeBaseViewSet,
    ChatConversationViewSet
)
from notificaciones.views import DeviceTokenViewSet, NotificacionViewSet

router = DefaultRouter()
router.register(r'eventos', EventoViewSet, basename='evento')
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'chatbot-knowledge', ChatbotKnowledgeBaseViewSet, basename='chatbot-knowledge')
router.register(r'chatbot-conversations', ChatConversationViewSet, basename='chatbot-conversations')
router.register(r'notifications', NotificacionViewSet, basename='notification')
router.register(r'fcm-token', DeviceTokenViewSet, basename='fcm-token')


urlpatterns = [
    path('', include(router.urls)),
    
    # Rutas de Autenticación y Usuarios
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', UserRegistrationView.as_view(), name='user_register'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),

    # Rutas de Chatbot Corporativo
    path('chatbot/query/', ChatbotQueryView.as_view(), name='chatbot_query'),
    path('chatbot/recommended-questions/', ChatbotRecommendedQuestionsView.as_view(), name='recommended_questions'),
    
] 