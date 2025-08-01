from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class DNIAuthBackend(ModelBackend):
    """
    Backend de autenticación personalizado para iniciar sesión con DNI.
    
    Permite usar el DNI del usuario en el campo 'username' del formulario de
    login para la autenticación, en lugar del nombre de usuario tradicional.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Sobrescribe el método de autenticación para buscar por DNI.
        Retorna None en caso de fallo, siguiendo la convención de Django.
        """
        if username is None or password is None:
            return None
            
        UserModel = get_user_model()
        try:
            # El campo 'username' del modelo User almacena el DNI.
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            # Si el usuario no existe, retornamos None (estándar de Django)
            return None

        # Verificamos la contraseña.
        if not user.check_password(password):
            # Si la contraseña es incorrecta, retornamos None
            return None

        # Verificamos si el usuario está activo.
        if not getattr(user, "is_active", True):
            # Si está inactivo, también retornamos None
            return None

        # Si todo es correcto, devolvemos el usuario.
        return user

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None 