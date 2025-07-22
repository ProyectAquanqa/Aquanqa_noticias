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

        Args:
            username (str): El DNI del usuario.
            password (str): La contraseña del usuario.
        
        Returns:
            User or None: La instancia del usuario si la autenticación es exitosa.
        """
        UserModel = get_user_model()
        try:
            # El campo 'username' del modelo User almacena el DNI.
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            return None

        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None 