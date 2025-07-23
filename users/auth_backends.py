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
        # --- DEBUGGING START ---
        print("\n--- DNIAuthBackend: Intentando autenticar ---")
        print(f"Username (DNI) recibido: '{username}'")
        # No imprimir la contraseña en producción, pero para debug es útil
        print(f"Password recibida: '{password}'")
        # --- DEBUGGING END ---
        
        UserModel = get_user_model()
        try:
            # El campo 'username' del modelo User almacena el DNI.
            user = UserModel.objects.get(username=username)
            # --- DEBUGGING START ---
            print(f"Usuario encontrado en DB: {user.username}")
            # --- DEBUGGING END ---
        except UserModel.DoesNotExist:
            # --- DEBUGGING START ---
            print("Usuario NO encontrado en la base de datos.")
            print("--- Fin de DNIAuthBackend ---\n")
            # --- DEBUGGING END ---
            return None

        # --- DEBUGGING START ---
        password_is_correct = user.check_password(password)
        print(f"Resultado de user.check_password(): {password_is_correct}")
        
        user_is_active = getattr(user, "is_active", True)
        print(f"Estado de user.is_active: {user_is_active}")
        # --- DEBUGGING END ---
        
        if password_is_correct and user_is_active:
            print("¡Éxito! Contraseña correcta y usuario activo. Devolviendo usuario.")
            print("--- Fin de DNIAuthBackend ---\n")
            return user
            
        print("Fallo de autenticación: contraseña incorrecta o usuario inactivo.")
        print("--- Fin de DNIAuthBackend ---\n")
        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None 