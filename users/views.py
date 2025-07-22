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

@extend_schema(exclude=True)
class DniTokenObtainPairView(TokenObtainPairView):
    """
    Vista de login que acepta DNI y contraseña para devolver un token JWT.
    """
    serializer_class = DniTokenObtainPairSerializer

@extend_schema(
    tags=['Usuarios'],
    summary="Ver o actualizar el perfil del usuario autenticado",
    responses={200: ProfileSerializer}
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Permite a los usuarios autenticados ver y actualizar su perfil.
    Aquí pueden subir o cambiar la imagen de su firma.
    """
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Devuelve el perfil del usuario que realiza la petición."""
        return self.request.user.profile

    def perform_update(self, serializer):
        """Asegura que el campo 'updated_by' se actualice al modificar el perfil."""
        serializer.save(updated_by=self.request.user)

@extend_schema(
    summary="Registrar un nuevo usuario (Admin)",
    request=UserRegistrationSerializer,
    responses={
        201: OpenApiResponse(description="Usuario creado exitosamente", response=UserRegistrationSerializer),
        400: OpenApiResponse(description="Datos inválidos (p.ej. DNI no encontrado, error de API externa, etc.)"),
        403: OpenApiResponse(description="No tienes permiso para realizar esta acción (solo Admins).")
    }
)
class UserRegistrationView(generics.CreateAPIView):
    """
    Endpoint para registrar un nuevo usuario en el sistema.
    Solo accesible por usuarios en el grupo 'Admin'.
    Al proporcionar un DNI válido, los nombres y apellidos se autocompletan.
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
