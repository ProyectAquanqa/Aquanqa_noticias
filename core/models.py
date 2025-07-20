from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class BaseModelWithAudit(models.Model):
    """
    Modelo base abstracto que añade campos de auditoría:
    - Fechas de creación y actualización automáticas.
    - Usuario que creó y que actualizó por última vez el registro.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_created_by',
        verbose_name="Creado por"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_updated_by',
        verbose_name="Actualizado por"
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']
