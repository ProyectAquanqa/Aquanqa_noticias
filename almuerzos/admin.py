from django.contrib import admin
from .models import Almuerzo
from core.admin import AuditModelAdmin


@admin.register(Almuerzo)
class AlmuerzoAdmin(AuditModelAdmin):
    """
    Administración optimizada para el modelo Almuerzo.
    
    Interfaz limpia y funcional para gestionar menús diarios
    con herramientas de filtrado y búsqueda eficientes.
    """
    
    # Lista optimizada con información clave
    list_display = (
        'fecha', 'nombre_dia', 'entrada', 'plato_fondo', 
        'active', 'es_feriado', 'has_diet_menu', 'created_at'
    )
    
    # Filtros inteligentes para administradores
    list_filter = ('active', 'es_feriado', 'fecha', 'created_at')
    
    # Búsqueda en todos los campos de menú
    search_fields = ('entrada', 'plato_fondo', 'refresco', 'dieta')
    
    # Campos de solo lectura para auditoría
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')
    
    # Ordenamiento por fecha
    ordering = ['fecha']
    
    # Jerarquía por fecha para navegación fácil
    date_hierarchy = 'fecha'
    
    # Organización clara de campos en formulario
    fieldsets = (
        ('Información del Menú', {
            'fields': ('fecha', 'entrada', 'plato_fondo', 'refresco', 'dieta'),
            'description': 'Detalles del menú del día'
        }),
        ('Disponibilidad y Control', {
            'fields': ('active', 'es_feriado', 'link'),
            'description': 'Control de disponibilidad y enlaces'
        }),
        ('Información de Auditoría', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'Información de seguimiento automático'
        }),
    )
    
    # Métodos para mostrar información calculada
    def nombre_dia(self, obj):
        """Muestra el nombre del día en la lista."""
        return obj.nombre_dia()
    nombre_dia.short_description = 'Día'
    
    def has_diet_menu(self, obj):
        """Indica si tiene menú de dieta."""
        return obj.has_diet_menu
    has_diet_menu.boolean = True
    has_diet_menu.short_description = 'Dieta'