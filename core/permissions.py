from rest_framework import permissions

class IsInGroup(permissions.BasePermission):
    """
    Permiso personalizado para verificar si un usuario pertenece a uno o más grupos.
    Uso: permissions.IsInGroup('Admin', 'Manager')
    """
    def __init__(self, *groups):
        self.groups = groups

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Comprueba si el usuario pertenece a alguno de los grupos requeridos
        user_groups = request.user.groups.values_list('name', flat=True)
        return any(group in user_groups for group in self.groups)

class IsOwner(permissions.BasePermission):
    """
    Permiso personalizado para permitir solo al dueño de un objeto
    realizar una acción sobre él.
    Asume que el objeto tiene un campo `user`.
    """
    def has_object_permission(self, request, view, obj):
        # El permiso solo se concede si el usuario del objeto es el mismo que el usuario de la petición
        return obj.user == request.user 