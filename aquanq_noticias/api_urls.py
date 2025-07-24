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
from eventos.views import EventoViewSet, EventoFeedView
from notificaciones.views import DeviceTokenViewSet, NotificacionViewSet
from chatbot.views import (
    ChatbotKnowledgeBaseViewSet, ChatbotQueryView, ChatConversationViewSet,
    RecommendedQuestionsView
)
from users.views import UserViewSet, CustomTokenObtainPairView, CustomTokenRefreshView

# Configuración del router para ViewSets
router = DefaultRouter()
router.register(r'eventos', EventoViewSet, basename='evento')
router.register(r'knowledge', ChatbotKnowledgeBaseViewSet, basename='knowledge')
router.register(r'history', ChatConversationViewSet, basename='history')
router.register(r'devices', DeviceTokenViewSet, basename='devicetoken')
router.register(r'notifications', NotificacionViewSet, basename='notificacion')
router.register(r'users', UserViewSet, basename='user')

# Definición de patrones de URL
urlpatterns = [
    path('', include(router.urls)),
    
    # Rutas de autenticación
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    
    # Rutas del chatbot
    path('chatbot/', ChatbotQueryView.as_view(), name='chatbot-query'),
    path('chatbot/recommended-questions/', RecommendedQuestionsView.as_view(), name='chatbot-recommended-questions'),
    
    # Rutas de feed
    path('feed/', EventoFeedView.as_view(), name='evento-feed'),
] 