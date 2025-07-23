"""
Configuración ASGI para el proyecto AquanQ Noticias.

Para más información sobre ASGI, ver:
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aquanq_noticias.settings')

application = get_asgi_application()
