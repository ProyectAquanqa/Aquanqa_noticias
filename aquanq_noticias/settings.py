"""
Configuración de Django para el proyecto AquanQ.

Para más información, consulta la documentación de Django:
https://docs.djangoproject.com/en/5.2/topics/settings/
"""

import os
import environ
from pathlib import Path
from datetime import timedelta


BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(str(BASE_DIR.joinpath('.env')))


SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = ['172.16.11.29', '127.0.0.1', 'localhost', '192.168.18.13']

# Configuración de CORS (Cross-Origin Resource Sharing)
CORS_ALLOW_ALL_ORIGINS = True




# Application definition

AUTH_USER_MODEL = 'users.Usuario'

INSTALLED_APPS = [
    # Core de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Aplicaciones locales
    'core.apps.CoreConfig',
    'eventos.apps.EventosConfig',
    'chatbot.apps.ChatbotConfig',
    'users.apps.UsersConfig',
    'notificaciones.apps.NotificacionesConfig',
    'almuerzos.apps.AlmuerzosConfig',

    # Librerías de terceros
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    'django_filters',
]

# Configuración del modelo de usuario personalizado
AUTH_USER_MODEL = 'users.Usuario'


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # Debe estar antes de CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'aquanq_noticias.urls'
WSGI_APPLICATION = 'aquanq_noticias.wsgi.application'


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


# Base de Datos
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
    }
}


AUTHENTICATION_BACKENDS = [
    'users.auth_backends.DNIAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True


# Archivos Estáticos y de Medios
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Configuración de Django REST Framework (DRF)
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}

# Configuración de JWT (JSON Web Token)
# Configuración optimizada para aplicaciones móviles con sesiones persistentes
SIMPLE_JWT = {
    # Access token más duradero para mejor UX móvil (4 horas)
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=4),
    
    # Refresh token de larga duración para sesiones persistentes (7 días)
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    
    # Rotación habilitada para seguridad pero con tokens más duraderos
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    
    # Configuraciones adicionales para mejor manejo móvil
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    # Headers
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    
    # Sliding tokens deshabilitado para usar rotación
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# Configuración de drf-spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'AquanQ Noticias API',
    'DESCRIPTION': 'Documentación de la API para el proyecto AquanQ Noticias',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'TAGS': [
        {'name': 'Autenticación', 'description': 'Endpoints para iniciar sesión y gestionar tokens.'},
        {'name': 'Usuarios', 'description': 'Endpoints para la gestión de usuarios y perfiles.'},
        {'name': 'Eventos', 'description': 'Endpoints para la gestión de eventos, noticias y reconocimientos.'},
        {'name': 'Chatbot', 'description': 'Endpoints públicos para la interacción con el chatbot.'},
        {'name': 'Knowledge', 'description': 'Endpoints para la gestión del conocimiento del chatbot.'},
        {'name': 'Chat History', 'description': 'Endpoints para la consulta del historial de conversaciones del chatbot.'},
        {'name': 'Notificaciones', 'description': 'Endpoints para la gestión de notificaciones push y dispositivos.'},
    ],
}

# API externa para la consulta de DNI.
DNI_API_URL = "https://aplicativo.aquanqa.net/api/consulta-dni/"
DNI_API_BEARER_TOKEN = env('DNI_API_BEARER_TOKEN')

# Firebase Cloud Messaging (FCM) para notificaciones push.
# La inicialización se realiza en notificaciones/apps.py
FIREBASE_ADMIN_CREDENTIALS_PATH = env('FIREBASE_ADMIN_CREDENTIALS_PATH', default=str(BASE_DIR / 'firebase-credentials.json'))
