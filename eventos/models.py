from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModelWithAudit


class Categoria(BaseModelWithAudit):
    """
    Categoría para clasificar los eventos (e.g., 'Noticias', 'Reconocimientos').
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
    Representa un valor de la empresa para los eventos de tipo 'Reconocimiento'.
    
    Permite asociar una insignia visual a cada valor.
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
    """
    Modelo principal que representa un evento, noticia o reconocimiento.
    """
    titulo = models.CharField(max_length=200)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos"
    )
    valor = models.ForeignKey(
        Valor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reconocimientos",
        help_text="Asociar solo si el evento es un 'Reconocimiento'."
    )
    descripcion = models.TextField()
    fecha = models.DateTimeField(db_index=True)
    imagen = models.ImageField(upload_to='eventos_imagenes/', blank=True, null=True)
    publicado = models.BooleanField(default=False, db_index=True)
    is_pinned = models.BooleanField(default=False, db_index=True, help_text="Fija el evento al inicio del feed.")
    autor = models.ForeignKey(User, on_delete=models.PROTECT, related_name="eventos_creados")

    class Meta:
        ordering = ['-fecha']
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"

    def __str__(self):
        return self.titulo
