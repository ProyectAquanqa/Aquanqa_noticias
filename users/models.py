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

    def save(self, *args, **kwargs):
        # Primero, obtenemos el estado del objeto antes de guardarlo
        if self.pk:  # Si el objeto ya tiene una clave primaria, significa que ya existe
            try:
                old_instance = Usuario.objects.get(pk=self.pk)
                
                # Comprobar si la foto de perfil ha cambiado y eliminar la antigua
                if old_instance.foto_perfil and self.foto_perfil != old_instance.foto_perfil:
                    old_instance.foto_perfil.delete(save=False)
                
                # Comprobar si la firma ha cambiado y eliminar la antigua
                if old_instance.firma and self.firma != old_instance.firma:
                    old_instance.firma.delete(save=False)
                    
            except Usuario.DoesNotExist:
                # Si por alguna razón el objeto no se encuentra, no hacemos nada
                pass
        
        # Llamar al método save original para que el guardado se complete
        super().save(*args, **kwargs)
