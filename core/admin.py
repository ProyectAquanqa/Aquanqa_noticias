from django.contrib import admin

class AuditModelAdmin(admin.ModelAdmin):
    """
    Clase base para el Admin de Django que automáticamente guarda
    quién creó y quién modificó por última vez un objeto.
    """
    def save_model(self, request, obj, form, change):
        """
        Al guardar un objeto desde el admin, asigna el usuario actual
        a los campos de auditoría.
        """
        if not change: # Si es un objeto nuevo
            obj.created_by = request.user
        
        obj.updated_by = request.user
        super().save_model(request, obj, form, change) 