from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .services import consultar_dni, DniNotFoundError, DniApiNotAvailableError
from .models import Profile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class DniTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializador para el login que personaliza el campo 'username' a 'dni'.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Renombra el campo 'username' a 'dni' en la respuesta de la API
        # para que sea más intuitivo para los clientes de la API.
        self.fields[self.username_field] = serializers.CharField(write_only=True)
        self.fields[self.username_field].label = 'dni'


class ProfileSerializer(serializers.ModelSerializer):
    """Serializador para ver y actualizar el perfil de un usuario."""
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Profile
        fields = ['foto_perfil', 'firma', 'created_by', 'updated_by']

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