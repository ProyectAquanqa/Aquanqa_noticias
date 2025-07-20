from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class DNIAuthBackend(ModelBackend):
    """
    Backend de autenticación que permite a los usuarios iniciar sesión
    utilizando su número de DNI en lugar de un nombre de usuario.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        # Django pasa el primer campo del formulario de login como 'username'
        # Aquí lo tratamos como si fuera el DNI.
        try:
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