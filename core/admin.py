from django.contrib import admin

class AuditModelAdmin(admin.ModelAdmin):
    """
    Clase base para el Admin que asigna automáticamente el usuario actual
    a los campos de auditoría al guardar un objeto.

    Hereda de esta clase en tus `admin.ModelAdmin` para modelos que usen
    `BaseModelWithAudit`.
    """
    def save_model(self, request, obj, form, change):
        """
        Asigna el usuario de la petición a los campos de auditoría.
        
        Args:
            request: La petición HTTP.
            obj: La instancia del modelo que se guarda.
            form: El formulario de admin.
            change (bool): True si el objeto está siendo modificado.
        """
        if not obj.pk:  # Si es un objeto nuevo (pk aún no existe)
            obj.created_by = request.user
        
        obj.updated_by = request.user
        super().save_model(request, obj, form, change) 