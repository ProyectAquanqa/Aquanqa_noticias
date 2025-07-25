from django.contrib.auth.models import AbstractUser
from django.db import models
from core.models import BaseModelWithAudit

# Create your models here.

class Usuario(AbstractUser, BaseModelWithAudit):
    """
    Modelo de Usuario Personalizado.
    Hereda de AbstractUser para la autenticación y BaseModelWithAudit para la auditoría.
    """
    # AbstractUser ya incluye: username, first_name, last_name, email, is_staff, is_active, date_joined
    
    foto_perfil = models.ImageField(
        upload_to='fotos_perfil/',
        null=True,
        blank=True
    )
    firma = models.ImageField(
        upload_to='firmas_usuarios/',
        null=True,
        blank=True,
        help_text="Firma digitalizada del usuario."
    )

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.username
