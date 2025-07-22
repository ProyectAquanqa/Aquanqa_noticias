from rest_framework import permissions

class IsInGroup(permissions.BasePermission):
    """
    Permiso personalizado para verificar si un usuario pertenece a un grupo.

    Se inicializa con los nombres de los grupos requeridos.
    Uso: `permission_classes = [IsInGroup('Admin', 'Ventas')]`
    """
    def __init__(self, *groups):
        self.groups = groups

    def has_permission(self, request, view):
        """
        Comprueba si el usuario autenticado pertenece a alguno de los grupos.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_groups = request.user.groups.values_list('name', flat=True)
        # Devuelve True si hay alguna intersección entre los grupos del usuario y los requeridos.
        return any(group in user_groups for group in self.groups)

class IsOwner(permissions.BasePermission):
    """
    Permiso personalizado para permitir acceso solo al propietario del objeto.

    Asume que el modelo de objeto (`obj`) tiene un campo `user` que lo relaciona
    con el modelo `User`.
    """
    def has_object_permission(self, request, view, obj):
        """
        Comprueba si `obj.user` es el mismo que `request.user`.
        """
        return obj.user == request.user 