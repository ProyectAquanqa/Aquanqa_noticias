from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .exceptions import UserNotFound, InvalidPassword

class DNIAuthBackend(ModelBackend):
    """
    Backend de autenticación personalizado para iniciar sesión con DNI.
    
    Permite usar el DNI del usuario en el campo 'username' del formulario de
    login para la autenticación, en lugar del nombre de usuario tradicional.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Sobrescribe el método de autenticación para buscar por DNI y lanzar excepciones específicas.
        """
        UserModel = get_user_model()
        try:
            # El campo 'username' del modelo User almacena el DNI.
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            # Si el usuario no existe, lanzamos la excepción personalizada.
            raise UserNotFound()

        # Verificamos la contraseña.
        if not user.check_password(password):
            # Si la contraseña es incorrecta, lanzamos la otra excepción.
            raise InvalidPassword()

        # Verificamos si el usuario está activo.
        if not getattr(user, "is_active", True):
            # Si está inactivo, también es un fallo de autenticación.
            # Podemos usar la misma excepción que para la contraseña incorrecta.
            raise InvalidPassword('El usuario está inactivo.')

        # Si todo es correcto, devolvemos el usuario.
        return user

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None 