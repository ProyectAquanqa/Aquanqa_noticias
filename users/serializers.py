from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib.auth.models import Group
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .services import consultar_dni, DniNotFoundError, DniApiNotAvailableError

Usuario = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer de token personalizado para añadir datos del usuario a la respuesta.
    """
    def validate(self, attrs):
        # La validación por defecto se encarga de la autenticación
        data = super().validate(attrs)

        # Añadir datos del usuario al diccionario de respuesta
        serializer = UsuarioSerializer(self.user)
        user_data = serializer.data
        
        # Renombramos claves para mantener compatibilidad con lo que la App Android espera
        # en la respuesta del login.
        data['user'] = {
            "id": user_data.get('id'),
            "first_name": user_data.get('first_name'),
            "dni": user_data.get('username')
        }
        
        return data


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo de Usuario personalizado.
    """
    groups = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Group.objects.all()
    )
    
    class Meta:
        model = Usuario
        fields = (
            'id', 'username', 'first_name', 'last_name', 'email', 
            'foto_perfil', 'firma', 'groups', 'is_staff', 'is_active', 'date_joined'
        )
        read_only_fields = ('is_staff', 'is_active', 'date_joined')

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro de nuevos usuarios a partir de su DNI.
    Orquesta la consulta a un servicio externo para autocompletar los datos
    y la creación del nuevo Usuario.
    """
    dni = serializers.CharField(write_only=True, max_length=8, min_length=8)

    class Meta:
        model = Usuario
        # El cliente solo necesita enviar 'dni' y 'password'.
        fields = ('dni', 'password')
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}},
        }

    def validate_dni(self, value):
        """
        Valida que el DNI sea numérico y no esté ya registrado en el sistema.
        """
        if not value.isdigit():
            raise serializers.ValidationError("El DNI debe contener solo dígitos.")
        if Usuario.objects.filter(username=value).exists():
            raise serializers.ValidationError("Un usuario con este DNI ya existe.")
        return value

    def create(self, validated_data):
        """
        Crea el usuario, autocompletando sus datos desde el servicio de DNI.
        """
        dni = validated_data.pop('dni')
        password = validated_data.pop('password')
        
        try:
            # 1. Consultar el servicio externo de DNI
            datos_dni = consultar_dni(dni)

            # El usuario que realiza la acción (si está disponible en el contexto)
            request = self.context.get('request')
            admin_user = request.user if request and request.user.is_authenticated else None

            with transaction.atomic():
                # 2. Crear el objeto Usuario con los datos autocompletados
                user = Usuario.objects.create_user(
                username=dni,
                    password=password,
                first_name=datos_dni.get('nombres', '').strip(),
                    last_name=f"{datos_dni.get('apellido_paterno', '')} {datos_dni.get('apellido_materno', '')}".strip(),
                    created_by=admin_user,
                    updated_by=admin_user
            )
            
                # 3. Asignar el grupo 'Trabajador' por defecto
            try:
                trabajador_group = Group.objects.get(name='Trabajador')
                user.groups.add(trabajador_group)
            except Group.DoesNotExist:
                    # Si el grupo no existe, es un problema de configuración del sistema.
                    # Se podría registrar un log o manejarlo de otra forma, pero por ahora
                    # la creación del usuario no se interrumpe.
                    pass

            return user

        except DniNotFoundError:
            raise serializers.ValidationError({"dni": "El DNI consultado no fue encontrado o no es válido."})
        except DniApiNotAvailableError:
            raise serializers.ValidationError(
                "El servicio de validación de DNI no está disponible en este momento. Intente más tarde."
            ) 