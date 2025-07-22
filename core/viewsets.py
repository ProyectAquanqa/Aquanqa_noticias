from rest_framework import viewsets

class AuditModelViewSet(viewsets.ModelViewSet):
    """
    Un `ModelViewSet` que asigna automáticamente información de auditoría.

    Extiende este ViewSet en lugar de `ModelViewSet` para que los campos
    `created_by` y `updated_by` se gestionen solos al usar la API,
    asumiendo que el serializador los acepta.
    """

    def perform_create(self, serializer):
        """
        Asigna el usuario de la petición a `created_by` y `updated_by` al crear.
        """
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        """
        Asigna el usuario de la petición a `updated_by` al actualizar.
        """
        serializer.save(updated_by=self.request.user) 