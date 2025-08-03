from django.contrib import admin
from .models import Almuerzo
from core.admin import AuditModelAdmin


@admin.register(Almuerzo)
class AlmuerzoAdmin(AuditModelAdmin):
    """
    Configuración del admin para el modelo Almuerzo.
    
    Hereda de AuditModelAdmin para funcionalidad de auditoría automática.
    Proporciona interfaz completa para gestionar menús diarios de almuerzo.
    """
    list_display = (
        'fecha', 
        'entrada', 
        'plato_fondo', 
        'refresco',
        'es_feriado', 
        'created_at', 
        'updated_at'
    )
    list_filter = ('es_feriado', 'fecha')
    search_fields = ('entrada', 'plato_fondo', 'refresco')
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')
    ordering = ['fecha']
    date_hierarchy = 'fecha'
    
    fieldsets = (
        ('Información del Menú', {
            'fields': ('fecha', 'entrada', 'plato_fondo', 'refresco', 'es_feriado', 'link')
        }),
        ('Información de Auditoría', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )