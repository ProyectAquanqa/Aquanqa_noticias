"""
Configuración de Django para el proyecto AquanQ Noticias.

Variables de entorno requeridas (.env):
- SECRET_KEY: Clave secreta de Django
- DEBUG: Booleano para modo debug (default: False)
- FIREBASE_ADMIN_CREDENTIALS_PATH: Ruta al archivo de credenciales de Firebase

Para más información sobre la configuración, ver:
https://docs.djangoproject.com/en/5.2/topics/settings/
"""

import os
import environ
import firebase_admin
from pathlib import Path
from firebase_admin import credentials

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Inicialización de variables de entorno
env = environ.Env()
environ.Env.read_env(str(BASE_DIR.joinpath('.env')))

# Configuración de seguridad
# ADVERTENCIA: Mantener la SECRET_KEY segura en producción
SECRET_KEY = env('SECRET_KEY')

# Backends de autenticación personalizados
AUTHENTICATION_BACKENDS = [
    'users.auth_backends.DNIAuthBackend',  # Autenticación personalizada con DNI
    'django.contrib.auth.backends.ModelBackend', 
]

# Configuración de modo debug
DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    # Aplicaciones del core de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Aplicaciones locales
    'core',  
    'eventos',  
    'chatbot', 
    'users',  
    'notificaciones', 

    # Aplicaciones de terceros
    'rest_framework', 
    'corsheaders',  
    'drf_spectacular', 
    'django_filters',
]

# Configuración de middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS - debe estar antes de CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'aquanq_noticias.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'aquanq_noticias.wsgi.application'

# Configuración de base de datos
# TODO: Mover credenciales a variables de entorno
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "aquanq_events",
        "USER": "root",
        "PASSWORD": "abcd123",
        "HOST": "127.0.0.1",
        "PORT": "3306",
    }
}

# Validadores de contraseña
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Configuración de internacionalización
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Configuración de archivos estáticos y media
STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración de CORS
# TODO: Restringir en producción
CORS_ALLOW_ALL_ORIGINS = True  # Solo para desarrollo

# Configuración de Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # TODO: Restringir en producción
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
}

# Configuración de Firebase Cloud Messaging (FCM)
FIREBASE_ADMIN_CREDENTIALS = os.getenv('FIREBASE_ADMIN_CREDENTIALS_PATH', BASE_DIR / 'firebase-credentials.json')

# Configuración de API DNI
DNI_API_URL = "https://aplicativo.aquanqa.net/api/consulta-dni/"
DNI_API_BEARER_TOKEN = "0d6924c7a31049297df548e0cb18390a7827c08b"  # TODO: Mover a variables de entorno

# Inicialización de Firebase
if os.path.exists(FIREBASE_ADMIN_CREDENTIALS):
    try:
        cred = credentials.Certificate(FIREBASE_ADMIN_CREDENTIALS)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK inicializado correctamente.")
    except Exception as e:
        print(f"ADVERTENCIA: El archivo de credenciales de Firebase existe, pero no se pudo inicializar el SDK. Error: {e}")
else:
    print("ADVERTENCIA: Archivo de credenciales de Firebase no encontrado. Las notificaciones push estarán desactivadas.")
