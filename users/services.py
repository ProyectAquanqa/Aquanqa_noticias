import requests
from django.conf import settings

# --- Excepciones Personalizadas para el Servicio ---

class DniServiceError(Exception):
    """Clase base para errores en el servicio de consulta de DNI."""
    pass

class DniApiNotAvailableError(DniServiceError):
    """Lanzada cuando la API externa no está disponible o falla."""
    pass

class DniNotFoundError(DniServiceError):
    """Lanzada cuando el DNI no se encuentra o no está autorizado."""
    pass

# --- Servicio Refactorizado ---

def consultar_dni(dni: str) -> dict:
    """
    Consulta la API externa para obtener los datos de un DNI.

    Args:
        dni: El número de DNI de 8 dígitos a consultar.

    Returns:
        Un diccionario con los datos del usuario si la consulta es exitosa.

    Raises:
        DniNotFoundError: Si el DNI no es encontrado o no está autorizado.
        DniApiNotAvailableError: Si hay un problema de conexión o un error
                                 inesperado con la API externa.
    """
    try:
        url = settings.DNI_API_URL
        token = settings.DNI_API_BEARER_TOKEN
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        body = {
            'idpropiedad_3638': dni
        }

        response = requests.post(url, headers=headers, json=body, timeout=10)
        response.raise_for_status() # Lanza HTTPError para respuestas 4xx/5xx

        # La API puede devolver 200 OK con una lista vacía si el DNI no existe
        if not response.json():
            raise DniNotFoundError(f"El DNI {dni} no fue encontrado en la API externa.")
        
        data = response.json()[0]

        return {
            'nombres': data['Nombres'],
            'apellido_paterno': data['A_Paterno'],
            'apellido_materno': data['A_Materno'],
        }

    except requests.exceptions.HTTPError as e:
        # Errores del lado del servidor o cliente (4xx, 5xx)
        raise DniApiNotAvailableError(f"La API de DNI devolvió un error: {e.response.status_code}") from e

    except requests.exceptions.RequestException as e:
        # Errores de conexión, timeout, etc.
        raise DniApiNotAvailableError(f"No se pudo conectar con la API de DNI: {e}") from e

    except (IndexError, KeyError) as e:
        # La respuesta de la API no tiene el formato esperado (p.ej. lista vacía o claves faltantes)
        raise DniApiNotAvailableError(f"La respuesta de la API de DNI no es válida: {e}") from e 