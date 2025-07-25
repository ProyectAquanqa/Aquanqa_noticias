from django.db import models
from django.conf import settings

# Create your models here.

class BaseModelWithAudit(models.Model):
    """
    Modelo base abstracto que añade campos de auditoría.

    Incluye fechas de creación/actualización automáticas y seguimiento
    del usuario que crea y modifica el registro. Debe ser heredado por otros
    modelos de la aplicación para mantener un registro de auditoría consistente.
    
    Atributos:
        created_at (DateTimeField): Fecha y hora de creación del registro.
        updated_at (DateTimeField): Fecha y hora de la última actualización.
        created_by (ForeignKey): Usuario que creó el registro.
        updated_by (ForeignKey): Usuario que realizó la última modificación.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_created_by',
        verbose_name="Creado por"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_updated_by',
        verbose_name="Actualizado por"
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']
