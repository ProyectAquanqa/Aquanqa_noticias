from django.apps import AppConfig
from django.conf import settings
import firebase_admin
from firebase_admin import credentials
import os


class NotificacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notificaciones'

    def ready(self):
        """
        Inicializa el SDK de Firebase Admin cuando la aplicación de notificaciones está lista.

        Este método es el lugar recomendado por Django para el código de inicialización,
        ya que se ejecuta una sola vez al arrancar el servidor.
        """
        if not firebase_admin._apps:
            try:
                cred_path = settings.FIREBASE_ADMIN_CREDENTIALS_PATH
                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    print("Firebase Admin SDK inicializado correctamente desde notificaciones.apps.")
                else:
                    print("ADVERTENCIA: Archivo de credenciales de Firebase no encontrado. Las notificaciones push estarán desactivadas.")
            except Exception as e:
                print(f"ADVERTENCIA: No se pudo inicializar Firebase Admin SDK. Error: {e}")
