"""
Configuración ASGI para el proyecto AquanQ Noticias.

Este módulo contiene la configuración ASGI (Asynchronous Server Gateway Interface) que permite
servir la aplicación Django a través de servidores web asíncronos como Daphne o Uvicorn.
ASGI proporciona soporte para operaciones asíncronas y WebSockets.

Para más información sobre ASGI, ver:
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aquanq_noticias.settings')

# Obtiene la aplicación ASGI para servir el proyecto
application = get_asgi_application()
