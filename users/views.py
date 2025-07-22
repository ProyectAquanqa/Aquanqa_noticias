from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from .serializers import UserRegistrationSerializer, ProfileSerializer, DniTokenObtainPairSerializer
from .models import Profile
from core.permissions import IsInGroup
from drf_spectacular.utils import extend_schema, OpenApiRequest, OpenApiResponse
from rest_framework_simplejwt.views import TokenObtainPairView

# Create your views here.

@extend_schema(tags=['Autenticación'])
class DniTokenObtainPairView(TokenObtainPairView):
    """
    Endpoint de login que acepta DNI y contraseña para obtener un token JWT.
    """
    serializer_class = DniTokenObtainPairSerializer

@extend_schema(tags=['Usuarios'])
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Permite a un usuario autenticado ver y actualizar su propio perfil.
    """
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Devuelve el perfil asociado al usuario que realiza la petición."""
        return self.request.user.profile

    def perform_update(self, serializer):
        """Añade el usuario actual a `updated_by` al modificar el perfil."""
        serializer.save(updated_by=self.request.user)

@extend_schema(tags=['Usuarios'])
class UserRegistrationView(generics.CreateAPIView):
    """
    Endpoint para registrar nuevos usuarios, accesible solo por Administradores.

    El `UserRegistrationSerializer` se encarga de la lógica de consultar
    el servicio de DNI y autocompletar los datos del usuario.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer

    
    def get_permissions(self):
        """
        Define los permisos para esta vista.
        """
        return [permissions.IsAuthenticated(), IsInGroup('Admin')]


@extend_schema(
    tags=['Usuarios'],
    summary="Verificar si un usuario existe por DNI",
    responses={
        200: OpenApiResponse(description="El usuario existe."),
        404: OpenApiResponse(description="El usuario no fue encontrado.")
    }
)
class UserExistsView(generics.GenericAPIView):
    """
    Endpoint público para verificar si un usuario con un DNI específico
    ya está registrado en el sistema.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        dni = kwargs.get('dni')
        if not dni:
            return Response({"detail": "DNI no proporcionado."}, status=status.HTTP_400_BAD_REQUEST)
        
        user_exists = User.objects.filter(username=dni).exists()

        if user_exists:
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
=======
    permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin')]
