"""
Configuración WSGI para el proyecto AquanQ Noticias.

Este módulo contiene la configuración WSGI (Web Server Gateway Interface) que permite
servir la aplicación Django a través de servidores web compatibles con WSGI como
uWSGI o Gunicorn.

Para más información sobre WSGI, ver:
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aquanq_noticias.settings')

# Obtiene la aplicación WSGI para servir el proyecto
application = get_wsgi_application()
