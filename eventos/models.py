from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModelWithAudit


class Categoria(BaseModelWithAudit):
    """
    Modelo para categorizar los eventos.
    Ej: Publicaciones, Reconocimientos, Noticias, etc.
    """
    nombre = models.CharField(max_length=100, unique=True, db_index=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Categoría de Evento"
        verbose_name_plural = "Categorías de Eventos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Valor(BaseModelWithAudit):
    """
    Modelo para los valores de la empresa que se pueden reconocer.
    Ej: Pasión, Visión de Futuro, etc.
    """
    nombre = models.CharField(max_length=100, unique=True, db_index=True)
    descripcion = models.TextField(blank=True, null=True)
    insignia = models.ImageField(
        upload_to='valores_insignias/', 
        blank=True, 
        null=True, 
        help_text="Icono o insignia que representa el valor."
    )

    class Meta:
        verbose_name = "Valor de la Empresa"
        verbose_name_plural = "Valores de la Empresa"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Evento(BaseModelWithAudit):
    titulo = models.CharField(max_length=200)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos",
        help_text="Categoría a la que pertenece el evento."
    )
    valor = models.ForeignKey(
        Valor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reconocimientos",
        help_text="Si este evento es un reconocimiento, asigna el valor correspondiente."
    )
    descripcion = models.TextField()
    fecha = models.DateTimeField(db_index=True)
    imagen = models.ImageField(upload_to='eventos_imagenes/', blank=True, null=True, help_text="Imagen principal del evento.")
    publicado = models.BooleanField(default=False, db_index=True)
    is_pinned = models.BooleanField(default=False, db_index=True, help_text="Marca esta opción para fijar el evento al inicio.")
    autor = models.ForeignKey(User, on_delete=models.PROTECT, related_name="eventos_creados")

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return self.titulo
