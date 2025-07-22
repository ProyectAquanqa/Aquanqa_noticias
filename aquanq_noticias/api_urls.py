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
from chatbot.views import ChatbotKnowledgeBaseViewSet, ChatbotQueryView, ChatConversationViewSet
from users.views import UserRegistrationView, UserProfileView, DniTokenObtainPairView, UserExistsView
from rest_framework_simplejwt.views import TokenRefreshView

# Configuración del router para ViewSets
router = DefaultRouter()
router.register(r'eventos', EventoViewSet, basename='evento')
router.register(r'knowledgebase', ChatbotKnowledgeBaseViewSet, basename='knowledgebase')
router.register(r'chat-history', ChatConversationViewSet, basename='chat-history')
router.register(r'devices', DeviceTokenViewSet, basename='devicetoken')
router.register(r'notificaciones', NotificacionViewSet, basename='notificacion')

# Definición de patrones de URL
# Incluye rutas para vistas basadas en clase y ViewSets
urlpatterns = [
    # Incluir todas las rutas generadas por el router
    path('', include(router.urls)),
    
    # Rutas específicas para vistas basadas en clase
    path('feed/', EventoFeedView.as_view(), name='evento-feed'),
    
    # Rutas de autenticación
    path('token/', DniTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Rutas del chatbot
    path('chatbot/', ChatbotQueryView.as_view(), name='chatbot-query'),
    
    # Rutas de gestión de usuarios
    path('users/register/', UserRegistrationView.as_view(), name='user-register'),
    path('profile/me/', UserProfileView.as_view(), name='user-profile'),
    # Nueva URL para verificar existencia de usuario
    path('users/exists/<str:dni>/', UserExistsView.as_view(), name='user-exists'),
] 