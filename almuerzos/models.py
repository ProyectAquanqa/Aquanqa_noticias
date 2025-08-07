from django.db import models
from core.models import BaseModelWithAudit


class Almuerzo(BaseModelWithAudit):
    """
    Modelo optimizado para gestionar menús diarios de almuerzo.
    
    Incluye campos para control de disponibilidad y menús especiales.
    Hereda auditoría automática del modelo base.
    """
    
    # Información básica del menú
    fecha = models.DateField(
        unique=True,
        verbose_name="Fecha",
        help_text="Fecha del almuerzo"
    )
    entrada = models.CharField(
        max_length=100,
        verbose_name="Entrada",
        help_text="Plato de entrada"
    )
    plato_fondo = models.CharField(
        max_length=100,
        verbose_name="Plato de fondo", 
        help_text="Plato principal"
    )
    refresco = models.CharField(
        max_length=50,
        verbose_name="Refresco",
        help_text="Bebida del menú"
    )
    
    # Campos de disponibilidad y control
    es_feriado = models.BooleanField(
        default=False,
        verbose_name="Es feriado",
        help_text="Día sin servicio por feriado"
    )
    active = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Almuerzo disponible para pedidos"
    )
    
    # Campos opcionales
    link = models.URLField(
        blank=True,
        null=True,
        verbose_name="Link de pedido",
        help_text="URL para realizar pedidos"
    )
    dieta = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Dieta",
        help_text="Menú especial de dieta"
    )

    class Meta:
        ordering = ['fecha']
        verbose_name = "Almuerzo"
        verbose_name_plural = "Almuerzos"
        
    def __str__(self):
        """Representación clara del almuerzo."""
        estado = "Feriado" if self.es_feriado else ("Activo" if self.active else "Inactivo")
        return f"{self.nombre_dia()} - {self.fecha} ({estado})"

    def nombre_dia(self):
        """Nombre del día en español."""
        dias_es = {
            "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
            "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", 
            "Sunday": "Domingo"
        }
        return dias_es.get(self.fecha.strftime("%A"), "Día desconocido")
    
    def fecha_formateada(self):
        """Fecha formateada como 'Lunes 18 de agosto' para la UI."""
        meses_es = {
            1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
            5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
            9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
        }
        
        nombre_dia = self.nombre_dia()
        dia = self.fecha.day
        mes = meses_es.get(self.fecha.month, "enero")
        
        return f"{nombre_dia} {dia} de {mes}"
    
    @property
    def is_available(self):
        """Verifica si está disponible para pedidos."""
        return self.active and not self.es_feriado
    
    @property
    def has_diet_menu(self):
        """Verifica si tiene menú de dieta."""
        return bool(self.dieta)