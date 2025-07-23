from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import User, Profile
from .serializers import UserRegistrationSerializer, ProfileSerializer, CustomTokenObtainPairSerializer
from rest_framework.decorators import action, parser_classes
from django.contrib.auth.hashers import make_password

# Vista personalizada para la obtención de tokens JWT
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista de obtención de token que utiliza un serializador personalizado para
    proporcionar mensajes de error de autenticación más claros y específicos.

    Hereda de la vista estándar de Simple JWT pero la configura para usar
    `CustomTokenObtainPairSerializer`.
    """
    serializer_class = CustomTokenObtainPairSerializer

# ViewSet para manejar el registro y perfiles de usuarios
class UserViewSet(viewsets.ViewSet):
    """
    Un ViewSet para manejar el registro de usuarios y la gestión de perfiles.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
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

    @action(detail=False, methods=['get', 'put'], 
            permission_classes=[permissions.IsAuthenticated],
            parser_classes=[MultiPartParser, FormParser])
    def profile(self, request):
        """
        Permite a un usuario ver o actualizar su propio perfil.
        Si el perfil no existe, lo crea automáticamente.
        """
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            # Si el perfil no existe, lo creamos automáticamente
            profile = Profile.objects.create(
                user=request.user,
                created_by=request.user,
                updated_by=request.user
            )
        
        if request.method == 'GET':
            serializer = ProfileSerializer(profile, context={'request': request})
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            print(f"DEBUG - Datos recibidos: {request.data}")
            print(f"DEBUG - Archivos recibidos: {request.FILES}")
            
            serializer = ProfileSerializer(profile, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid(raise_exception=True):
                # Manejar los archivos manualmente si es necesario
                if 'foto_perfil' in request.FILES:
                    profile.foto_perfil = request.FILES['foto_perfil']
                    print(f"DEBUG - Foto de perfil actualizada: {profile.foto_perfil.name}")
                if 'firma' in request.FILES:
                    profile.firma = request.FILES['firma']
                    print(f"DEBUG - Firma actualizada: {profile.firma.name}")
                
                # Guardar el perfil actualizado
                profile.updated_by = request.user
                profile.save()
                
                # Verificar los valores guardados
                print(f"DEBUG - Perfil guardado: foto_perfil={profile.foto_perfil.url if profile.foto_perfil else None}, firma={profile.firma.url if profile.firma else None}")
                
                # Devolver la respuesta actualizada
                serializer = ProfileSerializer(profile, context={'request': request})
                print(f"DEBUG - Respuesta serializada: {serializer.data}")
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['put'], 
            permission_classes=[permissions.IsAuthenticated],
            parser_classes=[JSONParser])
    def credentials(self, request):
        """
        Permite a un usuario actualizar su correo electrónico y/o contraseña.
        """
        user = request.user
        data = request.data
        changed = False
        
        # Debug para verificar los datos recibidos
        print(f"DEBUG - Datos para actualización de credenciales: {data}")
        
        # Actualizar email si se proporciona
        if 'email' in data and data['email']:
            user.email = data['email']
            changed = True
            print(f"DEBUG - Email actualizado a: {user.email}")
        
        # Actualizar contraseña si se proporciona
        if 'password' in data and data['password']:
            user.password = make_password(data['password'])
            changed = True
            print(f"DEBUG - Contraseña actualizada")
        
        # Guardar cambios si hubo alguno
        if changed:
            user.save()
            
        # Devolver los datos del perfil
        profile = user.profile
        serializer = ProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)
