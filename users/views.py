from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import UserRegistrationSerializer, UsuarioSerializer, CustomTokenObtainPairSerializer

Usuario = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista de obtención de token que utiliza el serializer personalizado
    para incluir datos del usuario en la respuesta.
    """
    serializer_class = CustomTokenObtainPairSerializer

class UserRegistrationView(generics.CreateAPIView):
    """
    Vista para registrar nuevos usuarios a partir de su DNI.
    Accesible solo por administradores (o personal autorizado).
    La lógica de consulta de DNI y creación se gestiona en el serializer.
    """
    queryset = Usuario.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.IsAdminUser] # O un permiso personalizado


class UserProfileView(APIView):
    """
    Vista para que los usuarios vean y actualicen su propio perfil.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Devuelve el perfil del usuario autenticado.
        """
        user = request.user
        serializer = UsuarioSerializer(user, context={'request': request})
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        """
        Actualiza parcialmente el perfil del usuario autenticado.
        Permite enviar solo los campos que se desean cambiar.
        """
        user = request.user
        # Pasamos `partial=True` para permitir actualizaciones parciales.
        serializer = UsuarioSerializer(user, data=request.data, partial=True, context={'request': request})
        
        if serializer.is_valid():
            # Guardamos los cambios y pasamos el usuario para la auditoría
            serializer.save(updated_by=request.user)
            return Response(serializer.data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
