from rest_framework import viewsets

class AuditModelViewSet(viewsets.ModelViewSet):
    """
    Un ModelViewSet personalizado que automáticamente añade información de auditoría
    (created_by y updated_by) al crear o actualizar objetos.
    """

    def perform_create(self, serializer):
        """
        Asigna el usuario actual al campo 'created_by' y 'updated_by'
        al crear un nuevo objeto.
        """
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        """
        Asigna el usuario actual al campo 'updated_by' al actualizar un objeto.
        """
        serializer.save(updated_by=self.request.user) 