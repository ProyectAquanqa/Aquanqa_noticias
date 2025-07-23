from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from .services import consultar_dni, DniNotFoundError, DniApiNotAvailableError
from .models import Profile

User = get_user_model()

class UserSerializerForToken(serializers.ModelSerializer):
    """
    Serializador ligero para incluir información básica del usuario en la respuesta del token.
    """
    class Meta:
        model = User
        fields = ('id', 'first_name', 'dni')
        # Renombrar 'username' a 'dni' para que coincida con el modelo de Android.
        extra_kwargs = {
            'dni': {'source': 'username'}
        }


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Un serializador de token personalizado que:
    1. Valida la existencia del usuario antes de autenticar.
    2. Incluye datos básicos del usuario en la respuesta del token.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Añadir datos personalizados al token si es necesario (opcional)
        # token['first_name'] = user.first_name
        return token

    def validate(self, attrs):
        # El flujo de validación se mantiene igual
        data = super().validate(attrs)

        # Añadir la información del usuario a la respuesta final
        serializer = UserSerializerForToken(self.user)
        data['user'] = serializer.data
        
        return data


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializador para ver y actualizar el perfil de un usuario.
    Incluye información básica del usuario y su perfil.
    """
    # Campos del usuario
    id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    firstName = serializers.CharField(source='user.first_name', read_only=True)
    lastName = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    # Obtener los grupos/roles del usuario
    groups = serializers.SerializerMethodField()
    
    # Renombrar campos para coincidir con la app Android
    fotoPerfil = serializers.ImageField(source='foto_perfil', required=False)
    
    # Campos adicionales
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Profile
        fields = [
            'id', 'username', 'firstName', 'lastName', 'email', 
            'groups', 'fotoPerfil', 'firma', 'created_by', 'updated_by'
        ]
        extra_kwargs = {
            'firma': {'required': False},
        }
    
    def get_groups(self, obj):
        """Devuelve la lista de grupos/roles a los que pertenece el usuario."""
        return [group.name for group in obj.user.groups.all()]
        
    def to_representation(self, instance):
        """
        Personaliza la representación del perfil para incluir las URLs completas de los archivos.
        """
        ret = super().to_representation(instance)
        
        request = self.context.get('request')
        
        # Construir URLs absolutas para las imágenes si existen
        if instance.foto_perfil and request is not None:
            ret['fotoPerfil'] = request.build_absolute_uri(instance.foto_perfil.url) if instance.foto_perfil else None
            
        if instance.firma and request is not None:
            ret['firma'] = request.build_absolute_uri(instance.firma.url) if instance.firma else None
            
        return ret

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializador para registrar nuevos usuarios a partir de su DNI.
    
    Orquesta la validación del DNI, la consulta a un servicio externo para
    obtener los datos del usuario, y la creación del `User` y `Profile`.
    """
    dni = serializers.CharField(write_only=True, min_length=8, max_length=8)

    class Meta:
        model = User
        fields = ('id', 'password', 'dni')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_dni(self, value):
        """Valida que el DNI sea numérico y no esté ya registrado."""
        if not value.isdigit():
            raise serializers.ValidationError("El DNI debe contener solo dígitos.")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Un usuario con este DNI ya existe.")
        return value

    def create(self, validated_data):
        """
        Crea el usuario, su perfil y le asigna un rol por defecto.
        
        Pasos:
        1. Consulta el DNI en el servicio externo.
        2. Crea el objeto `User` con los datos obtenidos.
        3. Crea el `Profile` asociado.
        4. Asigna el grupo 'Trabajador' por defecto.
        """
        dni = validated_data.pop('dni')
        admin_user = self.context['request'].user
        
        try:
            datos_dni = consultar_dni(dni)

            user = User.objects.create_user(
                username=dni,
                password=validated_data['password'],
                first_name=datos_dni.get('nombres', '').strip(),
                last_name=f"{datos_dni.get('apellido_paterno', '')} {datos_dni.get('apellido_materno', '')}".strip()
            )
            
            Profile.objects.create(user=user, created_by=admin_user, updated_by=admin_user)

            try:
                trabajador_group = Group.objects.get(name='Trabajador')
                user.groups.add(trabajador_group)
            except Group.DoesNotExist:
                # Fallar de forma ruidosa si la configuración básica del sistema (grupos) no está presente.
                raise serializers.ValidationError(
                    "Error de configuración: El grupo 'Trabajador' no existe."
                )

            return user

        except DniNotFoundError:
            raise serializers.ValidationError({"dni": "DNI no encontrado o no autorizado."})
        except DniApiNotAvailableError:
            # Oculta los detalles del error interno al cliente de la API.
            raise serializers.ValidationError(
                "El servicio de validación no está disponible. Intente más tarde."
            ) 