from django.db import models
from django.conf import settings
from core.models import BaseModelWithAudit


class Categoria(BaseModelWithAudit):
    """
    Categoría para clasificar los eventos (e.g., 'Noticias', 'Reconocimientos').
    """
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Categoría de Evento"
        verbose_name_plural = "Categorías de Eventos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Evento(BaseModelWithAudit):
    """
    Modelo principal que representa un evento o noticia.
    """
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha = models.DateTimeField()
    publicado = models.BooleanField(default=False)
    is_pinned = models.BooleanField(
        default=False,
        verbose_name="Fijado",
        help_text="Marcar para mantener el evento al principio de la lista."
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='eventos'
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos'
    )
    imagen = models.ImageField(upload_to='eventos_imagenes/', null=True, blank=True)

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ['-is_pinned', '-fecha']

    def __str__(self):
        return self.titulo
