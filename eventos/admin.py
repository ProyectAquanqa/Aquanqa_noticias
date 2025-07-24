from django.contrib import admin
from .models import Evento, Categoria
from core.admin import AuditModelAdmin

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'publicado', 'fecha', 'autor', 'created_at', 'updated_at')
    list_filter = ('publicado', 'fecha', 'autor')
    search_fields = ('titulo', 'descripcion')
    readonly_fields = ('created_by', 'updated_by')

@admin.register(Categoria)
class CategoriaAdmin(AuditModelAdmin):
    list_display = ('nombre', 'created_at', 'updated_at')
    search_fields = ('nombre',)
    readonly_fields = ('created_by', 'updated_by')
