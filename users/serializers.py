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
    También maneja errores específicos para distinguir entre usuario no existe vs contraseña incorrecta.
    """
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        # Primero verificar si el usuario existe
        try:
            user = Usuario.objects.get(username=username)
        except Usuario.DoesNotExist:
            # Usuario no existe - mensaje específico
            raise serializers.ValidationError('Usuario no registrado')
        
        # Usuario existe, verificar si está activo
        if not user.is_active:
            raise serializers.ValidationError('Cuenta desactivada')
        
        # Usuario existe y está activo, verificar contraseña
        if not user.check_password(password):
            # Contraseña incorrecta - mensaje específico
            raise serializers.ValidationError('Contraseña incorrecta')
        
        # Si llegamos aquí, todo está correcto, usar validación original
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
    Incluye campos calculados para la interfaz de administración.
    """
    groups = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Group.objects.all()
    )
    
    # Campo para validar contraseña actual al cambiar contraseña
    current_password = serializers.CharField(write_only=True, required=False)
    
    # Campos calculados para el frontend
    full_name = serializers.SerializerMethodField()
    groups_count = serializers.SerializerMethodField()
    last_login_formatted = serializers.SerializerMethodField()
    date_joined_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = (
            'id', 'username', 'first_name', 'last_name', 'email', 'password', 'current_password',
            'foto_perfil', 'firma', 'groups', 'is_staff', 'is_active', 
            'date_joined', 'last_login', 'created_at', 'updated_at',
            'created_by', 'updated_by',
            # Campos calculados
            'full_name', 'groups_count', 'last_login_formatted', 'date_joined_formatted'
        )
        read_only_fields = ('date_joined', 'last_login', 'created_at', 'updated_at', 'created_by', 'updated_by')
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}},
        }
    
    def get_full_name(self, obj):
        """Retorna el nombre completo del usuario."""
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username
    
    def get_groups_count(self, obj):
        """Retorna el número de grupos del usuario."""
        return obj.groups.count()
    
    def get_last_login_formatted(self, obj):
        """Retorna la fecha de último login formateada."""
        if obj.last_login:
            return obj.last_login.strftime('%d/%m/%Y %H:%M')
        return 'Nunca'
    
    def get_date_joined_formatted(self, obj):
        """Retorna la fecha de registro formateada."""
        return obj.date_joined.strftime('%d/%m/%Y %H:%M')
    
    def create(self, validated_data):
        """
        Creación personalizada para manejar contraseñas y grupos.
        """
        groups_data = validated_data.pop('groups', None)
        password = validated_data.pop('password', None)
        
        # Crear usuario
        user = Usuario.objects.create_user(**validated_data)
        
        # Establecer contraseña si se proporciona
        if password:
            user.set_password(password)
            user.save()
        
        # Asignar grupos si se proporcionan
        if groups_data:
            user.groups.set(groups_data)
        
        return user
    
    def update(self, instance, validated_data):
        """
        Actualización personalizada para manejar grupos, contraseñas y validaciones.
        """
        groups_data = validated_data.pop('groups', None)
        password = validated_data.pop('password', None)
        current_password = validated_data.pop('current_password', None)
        
        # Si se intenta cambiar la contraseña, validar la contraseña actual
        if password:
            if not current_password:
                raise serializers.ValidationError({
                    'current_password': 'La contraseña actual es requerida para cambiar la contraseña.'
                })
            
            # Verificar que la contraseña actual es correcta
            if not instance.check_password(current_password):
                raise serializers.ValidationError({
                    'current_password': 'La contraseña actual es incorrecta.'
                })
        
        # Actualizar campos básicos (excepto contraseña que se maneja por separado)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Manejar contraseña por separado para asegurar el hash correcto
        if password:
            instance.set_password(password)
        
        # Actualizar grupos si se proporcionan
        if groups_data is not None:
            instance.groups.set(groups_data)
        
        instance.save()
        return instance

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