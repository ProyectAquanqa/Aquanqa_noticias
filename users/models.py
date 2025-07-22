from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModelWithAudit

# Create your models here.

class Profile(BaseModelWithAudit):
    """
    Extiende el modelo User de Django con campos adicionales.

    Utiliza una relación `OneToOneField` para vincular cada perfil a un
    único usuario del sistema.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
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
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"

    def __str__(self):
        return f"Perfil de {self.user.username}"
