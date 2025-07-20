from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .services import consultar_dni, DniNotFoundError, DniApiNotAvailableError
from .models import Profile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class DniTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Puedes añadir campos extra al payload del token si quieres
        # token['username'] = user.username
        return token

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cambiamos la etiqueta del campo de 'username' a 'dni'
        self.fields[self.username_field] = serializers.CharField(write_only=True)
        self.fields[self.username_field].label = 'dni'


class ProfileSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Profile
        fields = ['foto_perfil', 'firma', 'created_by', 'updated_by']

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializador para el registro de nuevos usuarios.
    Valida el DNI, consulta la API externa y crea el usuario usando el DNI como username.
    """
    dni = serializers.CharField(write_only=True, min_length=8, max_length=8)

    class Meta:
        model = User
        fields = ('id', 'password', 'dni') # Se elimina 'email' y 'username' del input
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_dni(self, value):
        """
        Valida que el DNI sea numérico y tenga 8 dígitos.
        """
        if not value.isdigit():
            raise serializers.ValidationError("El DNI debe contener solo dígitos.")
        
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con este DNI.")
            
        return value

    def create(self, validated_data):
        """
        Orquesta la creación del usuario y su perfil, y le asigna el rol por defecto.
        """
        dni = validated_data.pop('dni')
        # Es crucial obtener el usuario que hace la petición desde el contexto.
        # Esto es necesario para que la auditoría funcione correctamente.
        admin_user = self.context['request'].user
        
        try:
            # Paso 1: Validar el DNI contra el servicio externo.
            datos_dni = consultar_dni(dni)

            # Paso 2: Crear el objeto User de Django.
            # Usamos create_user para asegurar el hasheo correcto de la contraseña.
            user = User.objects.create_user(
                username=dni,
                password=validated_data['password'],
                first_name=datos_dni.get('nombres', '').strip(),
                last_name=f"{datos_dni.get('apellido_paterno', '')} {datos_dni.get('apellido_materno', '')}".strip()
            )
            
            # Paso 3: Crear el Perfil, pasando explícitamente el usuario de auditoría.
            # Esto reemplaza la antigua lógica de señales para asegurar la trazabilidad.
            Profile.objects.create(user=user, created_by=admin_user, updated_by=admin_user)

            # Paso 4: Asignar el grupo "Trabajador" por defecto.
            try:
                trabajador_group = Group.objects.get(name='Trabajador')
                user.groups.add(trabajador_group)
            except Group.DoesNotExist:
                # Si el grupo no existe, es un error crítico de configuración del sistema.
                # Es importante fallar de forma ruidosa en lugar de silenciosa.
                raise serializers.ValidationError({
                    "non_field_errors": "Error de configuración interna: El grupo 'Trabajador' no existe."
                })

            return user

        except DniNotFoundError:
            # Si el servicio nos dice que el DNI no se encontró, devolvemos un error claro.
            raise serializers.ValidationError({
                "dni": "Este DNI no fue encontrado o no pertenece a un trabajador autorizado."
            })
        except DniApiNotAvailableError as e:
            # Si el servicio de DNI falla por cualquier otra razón (caído, error, etc.)
            # logueamos el error real y devolvemos un mensaje genérico al usuario.
            print(f"Error de servicio de DNI: {e}")
            raise serializers.ValidationError({
                "non_field_errors": "El servicio de validación de DNI no está disponible. Por favor, intente más tarde."
            }) 