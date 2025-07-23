from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import User, Profile
from .serializers import UserRegistrationSerializer, ProfileSerializer, CustomTokenObtainPairSerializer
from rest_framework.decorators import action
from django.contrib.auth.hashers import make_password
from drf_spectacular.utils import extend_schema, OpenApiRequest, OpenApiResponse

# Vista personalizada para la obtención de tokens JWT
@extend_schema(
    tags=['Autenticación'],
    summary="Iniciar Sesión (Obtener Token)",
    description="Autentica a un usuario con su DNI y contraseña para obtener un par de tokens JWT (acceso y refresco)."
)
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista de obtención de token que utiliza un serializador personalizado para
    proporcionar mensajes de error de autenticación más claros y específicos.
    """
    serializer_class = CustomTokenObtainPairSerializer

@extend_schema(
    tags=['Autenticación'],
    summary="Refrescar Token de Acceso",
    description="Obtiene un nuevo token de acceso (access token) utilizando un token de refresco (refresh token) válido."
)
class CustomTokenRefreshView(TokenRefreshView):
    """
    Vista personalizada para refrescar el token que incluye la decoración
    para la documentación de la API y así agruparla correctamente.
    """
    pass

# ViewSet para manejar el registro y perfiles de usuarios
@extend_schema(tags=['Usuarios'])
class UserViewSet(viewsets.ViewSet):
    """
    Un ViewSet para manejar el registro de usuarios y la gestión de perfiles.
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        """Asigna permisos basados en la acción."""
        if self.action == 'register':
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Registrar Nuevo Usuario (Admin)",
        description="Crea un nuevo usuario en el sistema a partir de su DNI. Los nombres se autocompletan desde un servicio externo. Requiere permisos de Administrador."
    )
    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        Registra un nuevo usuario utilizando su DNI.
        """
        serializer = UserRegistrationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            return Response({
                "user_id": user.id,
                "dni": user.username,
                "message": "Usuario registrado exitosamente."
            }, status=status.HTTP_201_CREATED)

    @extend_schema(
        methods=['GET'],
        summary="Ver mi Perfil",
        description="Obtiene los detalles del perfil del usuario actualmente autenticado."
    )
    @extend_schema(
        methods=['PUT'],
        summary="Actualizar mi Perfil",
        description="Actualiza el perfil del usuario autenticado, permitiendo cambiar la foto de perfil y la firma."
    )
    @action(detail=False, methods=['get', 'put'])
    def profile(self, request):
        """
        Permite a un usuario ver (GET) o actualizar (PUT) su propio perfil.
        Si el perfil no existe al intentar acceder, se crea automáticamente.
        """
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(
                user=request.user,
                created_by=request.user,
                updated_by=request.user
            )
        
        if request.method == 'GET':
            serializer = ProfileSerializer(profile, context={'request': request})
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            serializer = ProfileSerializer(profile, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid(raise_exception=True):
                profile.updated_by = request.user
                profile.save()
                serializer = ProfileSerializer(profile, context={'request': request})
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        methods=['PUT'],
        summary="Actualizar mis Credenciales",
        description="Permite al usuario autenticado actualizar su correo electrónico y/o contraseña."
    )
    @action(detail=False, methods=['put'])
    def credentials(self, request):
        """
        Permite a un usuario actualizar su correo electrónico y/o contraseña.
        """
        user = request.user
        data = request.data
        changed = False
        
        if 'email' in data and data['email']:
            user.email = data['email']
            changed = True
        
        if 'password' in data and data['password']:
            user.password = make_password(data['password'])
            changed = True
        
        if changed:
            user.save()
            
        profile = user.profile
        serializer = ProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)
