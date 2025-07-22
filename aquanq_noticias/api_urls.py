from django.urls import path, include
from rest_framework.routers import DefaultRouter
from eventos.views import EventoViewSet, EventoFeedView
from notificaciones.views import DeviceTokenViewSet, NotificacionViewSet
from chatbot.views import ChatbotKnowledgeBaseViewSet, ChatbotQueryView, ChatConversationViewSet
from users.views import UserRegistrationView, UserProfileView, DniTokenObtainPairView, UserExistsView
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'eventos', EventoViewSet, basename='evento')
router.register(r'knowledgebase', ChatbotKnowledgeBaseViewSet, basename='knowledgebase')
router.register(r'chat-history', ChatConversationViewSet, basename='chat-history')
router.register(r'devices', DeviceTokenViewSet, basename='devicetoken')
router.register(r'notificaciones', NotificacionViewSet, basename='notificacion')

urlpatterns = [
    path('', include(router.urls)),
    path('feed/', EventoFeedView.as_view(), name='evento-feed'),
    path('token/', DniTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('chatbot/', ChatbotQueryView.as_view(), name='chatbot-query'),
    path('users/register/', UserRegistrationView.as_view(), name='user-register'),
    path('profile/me/', UserProfileView.as_view(), name='user-profile'),
    # Nueva URL para verificar existencia de usuario
    path('users/exists/<str:dni>/', UserExistsView.as_view(), name='user-exists'),
] 