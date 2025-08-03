from django.db import models
from core.models import BaseModelWithAudit


class Almuerzo(BaseModelWithAudit):
    """
    Modelo para gestionar los menús diarios de almuerzo.
    
    Hereda de BaseModelWithAudit para incluir campos de auditoría automáticos.
    Cada almuerzo está asociado a una fecha específica y contiene información
    del menú del día incluyendo entrada, plato de fondo y refresco.
    """
    fecha = models.DateField(
        unique=True,
        verbose_name="Fecha",
        help_text="Fecha exacta del almuerzo"
    )
    entrada = models.CharField(
        max_length=100,
        verbose_name="Entrada",
        help_text="Plato de entrada del menú"
    )
    plato_fondo = models.CharField(
        max_length=100,
        verbose_name="Plato de fondo",
        help_text="Plato principal del menú"
    )
    refresco = models.CharField(
        max_length=50,
        verbose_name="Refresco",
        help_text="Bebida incluida en el menú"
    )
    es_feriado = models.BooleanField(
        default=False,
        verbose_name="Es feriado",
        help_text="Indica si no se atiende ese día por ser feriado"
    )
    link = models.URLField(
        blank=True,
        null=True,
        verbose_name="Link de pedido",
        help_text="Link para hacer el pedido del almuerzo"
    )

    class Meta:
        ordering = ['fecha']
        verbose_name = "Almuerzo"
        verbose_name_plural = "Almuerzos"

    def __str__(self):
        """
        Representación string del almuerzo.
        
        Returns:
            str: Formato "Día - Fecha (Estado)" donde Estado es Feriado o Activo
        """
        dia = self.fecha.strftime('%A')
        estado = 'Feriado' if self.es_feriado else 'Activo'
        return f"{dia} - {self.fecha} ({estado})"

    def nombre_dia(self):
        """
        Retorna el nombre del día en español.
        
        Returns:
            str: Nombre del día de la semana en español
        """
        dias_es = {
            "Monday": "Lunes",
            "Tuesday": "Martes",
            "Wednesday": "Miércoles",
            "Thursday": "Jueves",
            "Friday": "Viernes",
            "Saturday": "Sábado",
            "Sunday": "Domingo"
        }
        return dias_es[self.fecha.strftime("%A")]