from rest_framework.exceptions import APIException
from rest_framework import status

class UserNotFound(APIException):
    """
    Excepción para cuando un usuario no es encontrado en la base de datos durante la autenticación.
    """
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'El usuario con el DNI proporcionado no fue encontrado.'
    default_code = 'user_not_found'

class InvalidPassword(APIException):
    """
    Excepción para cuando la contraseña proporcionada es incorrecta.
    """
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'La contraseña proporcionada es incorrecta.'
    default_code = 'invalid_password' 