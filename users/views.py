from rest_framework import generics, permissions, status, viewsets, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.http import HttpResponse
import csv
from django.utils import timezone
from .serializers import UserRegistrationSerializer, UsuarioSerializer, CustomTokenObtainPairSerializer
from .services import consultar_dni, DniNotFoundError, DniApiNotAvailableError
from core.viewsets import AuditModelViewSet
from core.permissions import IsInGroup

Usuario = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista de obtención de token que utiliza el serializer personalizado
    para incluir datos del usuario en la respuesta.
    """
    serializer_class = CustomTokenObtainPairSerializer

class UserRegistrationView(generics.CreateAPIView):
    """
    Vista para registrar nuevos usuarios a partir de su DNI.
    Accesible solo por administradores (o personal autorizado).
    La lógica de consulta de DNI y creación se gestiona en el serializer.
    """
    queryset = Usuario.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.IsAdminUser] # O un permiso personalizado


class UserProfileView(APIView):
    """
    Vista para que los usuarios vean y actualicen su propio perfil.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Devuelve el perfil del usuario autenticado.
        """
        user = request.user
        serializer = UsuarioSerializer(user, context={'request': request})
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        """
        Actualiza parcialmente el perfil del usuario autenticado.
        Permite enviar solo los campos que se desean cambiar.
        """
        user = request.user
        # Pasamos `partial=True` para permitir actualizaciones parciales.
        serializer = UsuarioSerializer(user, data=request.data, partial=True, context={'request': request})
        
        if serializer.is_valid():
            # Guardamos los cambios y pasamos el usuario para la auditoría
            serializer.save(updated_by=request.user)
            return Response(serializer.data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['User Management'])
class UsuarioViewSet(AuditModelViewSet):
    """
    ViewSet completo para gestión de usuarios.
    Permite CRUD completo con filtros, búsqueda y paginación.
    Solo accesible por administradores.
    """
    queryset = Usuario.objects.all().select_related('created_by', 'updated_by').prefetch_related('groups')
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin', 'QA')]  # ← AGREGADO ESTO
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_staff', 'groups__name']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['date_joined', 'last_login', 'first_name', 'last_name', 'username']
    ordering = ['-date_joined']  # Por defecto ordenar por más recientes
    
    def get_permissions(self):
        """
        Solo administradores pueden gestionar usuarios.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin')]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin', 'QA')]
        else:
            permission_classes = [permissions.IsAuthenticated, IsInGroup('Admin')]
        return [permission() if isinstance(permission, type) else permission for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        """
        Lista usuarios con filtros avanzados.
        Soporta exportación CSV con format=csv
        """
        try:
            # Filtros adicionales personalizados
            queryset = self.filter_queryset(self.get_queryset())
            
            # Filtro por rango de fechas si se proporciona
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            
            if date_from:
                queryset = queryset.filter(date_joined__gte=date_from)
            if date_to:
                queryset = queryset.filter(date_joined__lte=date_to)
            
            # Verificar si se solicita exportación CSV
            format_param = request.query_params.get('format')
            
            if format_param == 'csv':
                return self._export_to_csv(queryset)
            
            # Paginación para respuesta JSON normal
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'status': 'success',
                'data': {
                    'count': queryset.count(),
                    'results': serializer.data
                }
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error al obtener usuarios: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _export_to_csv(self, queryset):
        """
        Exporta los usuarios a un archivo CSV
        """
        try:
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="usuarios_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            
            # Configurar el writer CSV
            writer = csv.writer(response)
            
            # Escribir cabeceras
            headers = [
                'ID',
                'DNI',
                'Nombre',
                'Apellido',
                'Email',
                'Estado',
                'Staff',
                'Grupos',
                'Fecha Registro',
                'Último Acceso'
            ]
            writer.writerow(headers)
            
            # Escribir datos de usuarios
            for user in queryset:
                try:
                    grupos = ', '.join([group.name for group in user.groups.all()]) if user.groups.exists() else 'Sin grupos'
                    
                    row = [
                        user.id,
                        user.username,
                        user.first_name or '',
                        user.last_name or '',
                        user.email or 'Sin email',
                        'Activo' if user.is_active else 'Inactivo',
                        'Sí' if user.is_staff else 'No',
                        grupos,
                        user.date_joined.strftime('%d/%m/%Y %H:%M') if user.date_joined else '',
                        user.last_login.strftime('%d/%m/%Y %H:%M') if user.last_login else 'Nunca'
                    ]
                    writer.writerow(row)
                except Exception as e:
                    # Log error but continue with other users
                    continue
            
            return response
        except Exception as e:
            # Fallback: return JSON error
            return Response({
                'status': 'error',
                'message': f'Error al generar CSV: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        """
        Crear nuevo usuario. Solo para administradores.
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return Response({
                'status': 'success',
                'message': 'Usuario creado exitosamente',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error al crear usuario: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        """
        Obtener detalles de un usuario específico.
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({
                'status': 'success',
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error al obtener usuario: {str(e)}'
            }, status=status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        """
        Actualizar usuario completo.
        """
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            return Response({
                'status': 'success',
                'message': 'Usuario actualizado exitosamente',
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error al actualizar usuario: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """
        Eliminar usuario (soft delete - desactivar).
        """
        try:
            instance = self.get_object()
            # En lugar de eliminar, desactivamos el usuario
            instance.is_active = False
            instance.save(update_fields=['is_active'])
            
            return Response({
                'status': 'success',
                'message': 'Usuario desactivado exitosamente'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error al desactivar usuario: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def toggle_active_status(self, request, pk=None):
        """
        Cambiar estado activo/inactivo del usuario.
        """
        try:
            user = self.get_object()
            user.is_active = not user.is_active
            user.save(update_fields=['is_active'])
            
            status_text = 'activado' if user.is_active else 'desactivado'
            return Response({
                'status': 'success',
                'message': f'Usuario {status_text} exitosamente',
                'data': {'is_active': user.is_active}
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error al cambiar estado: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def permissions(self, request, pk=None):
        """
        Obtener permisos del usuario (grupos).
        """
        try:
            user = self.get_object()
            groups = user.groups.all()
            return Response({
                'status': 'success',
                'data': {
                    'groups': [{'id': group.id, 'name': group.name} for group in groups],
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser
                }
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error al obtener permisos: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Estadísticas generales de usuarios.
        """
        try:
            total_users = Usuario.objects.count()
            active_users = Usuario.objects.filter(is_active=True).count()
            inactive_users = total_users - active_users
            staff_users = Usuario.objects.filter(is_staff=True).count()
            
            # Usuarios por grupo
            groups_stats = []
            for group in Group.objects.all():
                group_count = group.user_set.count()
                groups_stats.append({
                    'group_name': group.name,
                    'user_count': group_count
                })
            
            return Response({
                'status': 'success',
                'data': {
                    'total_users': total_users,
                    'active_users': active_users,
                    'inactive_users': inactive_users,
                    'staff_users': staff_users,
                    'groups_statistics': groups_stats
                }
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error al obtener estadísticas: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def bulk_import(self, request):
        """
        Importación masiva de usuarios desde datos estructurados
        
        Expected payload:
        {
            "users": [
                {
                    "username": "12345678",
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "email": "juan@email.com",
                    "is_active": true,
                    "is_staff": false,
                    "groups": ["Admin", "Staff"]
                },
                ...
            ]
        }
        """
        try:
            users_data = request.data.get('users', [])
            
            if not users_data or not isinstance(users_data, list):
                return Response({
                    'status': 'error',
                    'message': 'Se requiere una lista de usuarios en el campo "users"'
                }, status=status.HTTP_400_BAD_REQUEST)

            imported_count = 0
            skipped_count = 0
            errors = []

            for index, user_data in enumerate(users_data):
                try:
                    # Validar campos requeridos
                    username = user_data.get('username', '').strip()
                    first_name = user_data.get('first_name', '').strip()
                    last_name = user_data.get('last_name', '').strip()
                    
                    if not username:
                        errors.append(f"Fila {index + 1}: DNI es requerido")
                        skipped_count += 1
                        continue
                        
                    if not first_name:
                        errors.append(f"Fila {index + 1}: Nombre es requerido")
                        skipped_count += 1
                        continue
                        
                    if not last_name:
                        errors.append(f"Fila {index + 1}: Apellido es requerido")
                        skipped_count += 1
                        continue

                    # Verificar si el usuario ya existe
                    if Usuario.objects.filter(username=username).exists():
                        errors.append(f"Fila {index + 1}: Usuario con DNI {username} ya existe")
                        skipped_count += 1
                        continue

                    # Crear usuario
                    email = user_data.get('email', '').strip()
                    is_active = user_data.get('is_active', True)
                    is_staff = user_data.get('is_staff', False)
                    
                    # Generar password temporal usando DNI
                    temp_password = f"{username}_temp"
                    
                    user = Usuario.objects.create_user(
                        username=username,
                        first_name=first_name,
                        last_name=last_name,
                        email=email if email else None,
                        password=temp_password,
                        is_active=is_active,
                        is_staff=is_staff,
                        created_by=request.user,
                        updated_by=request.user
                    )

                    # Asignar grupos si se proporcionan
                    groups_names = user_data.get('groups', [])
                    if groups_names and isinstance(groups_names, list):
                        from django.contrib.auth.models import Group
                        for group_name in groups_names:
                            try:
                                group = Group.objects.get(name=group_name.strip())
                                user.groups.add(group)
                            except Group.DoesNotExist:
                                errors.append(f"Fila {index + 1}: Grupo '{group_name}' no existe")

                    imported_count += 1

                except Exception as e:
                    errors.append(f"Fila {index + 1}: Error inesperado - {str(e)}")
                    skipped_count += 1
                    continue

            # Preparar respuesta
            response_data = {
                'status': 'success',
                'data': {
                    'imported': imported_count,
                    'skipped': skipped_count,
                    'total_processed': len(users_data),
                    'errors': errors[:10] if errors else []  # Limitar errores mostrados
                }
            }

            if imported_count == 0:
                response_data['status'] = 'warning'
                response_data['message'] = 'No se pudo importar ningún usuario'
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error interno durante la importación: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def test_csv(self, request):
        """
        Endpoint de prueba para verificar que CSV funciona
        """
        try:
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="test.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Test', 'CSV', 'Endpoint'])
            writer.writerow(['Funciona', 'Correctamente', '!'])
            writer.writerow(['Usuario', f'{request.user.username}'])
            writer.writerow(['Grupos', f'{[g.name for g in request.user.groups.all()]}'])
            
            return response
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error en test CSV: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def debug_permissions(self, request):
        """
        Debug de permisos del usuario actual
        """
        user_groups = [g.name for g in request.user.groups.all()]
        
        return Response({
            'user': request.user.username,
            'groups': user_groups,
            'is_staff': request.user.is_staff,
            'is_superuser': request.user.is_superuser,
            'required_groups': ['Admin', 'QA'],
            'has_permission': any(g in ['Admin', 'QA'] for g in user_groups)
        })
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def consultar_dni(self, request):
        """
        Consulta datos de un DNI usando el servicio externo
        """
        dni = request.data.get('dni', '').strip()
        
        # Validaciones básicas
        if not dni:
            return Response({
                'status': 'error',
                'message': 'DNI requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not dni.isdigit() or len(dni) != 8:
            return Response({
                'status': 'error',
                'message': 'DNI debe tener exactamente 8 dígitos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Usar el servicio de consulta DNI
            datos_dni = consultar_dni(dni)
            
            return Response({
                'status': 'success',
                'data': {
                    'dni': dni,
                    'nombres': datos_dni['nombres'],
                    'apellido_paterno': datos_dni['apellido_paterno'],
                    'apellido_materno': datos_dni['apellido_materno'],
                    'full_name': f"{datos_dni['nombres']} {datos_dni['apellido_paterno']} {datos_dni['apellido_materno']}".strip()
                }
            })
            
        except DniNotFoundError as e:
            return Response({
                'status': 'error',
                'message': f'DNI no encontrado: {str(e)}'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except DniApiNotAvailableError as e:
            return Response({
                'status': 'error',
                'message': f'Servicio de DNI no disponible: {str(e)}'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def available_groups(self, request):
        """
        Obtiene todos los grupos disponibles para asignar a usuarios
        """
        try:
            groups = Group.objects.all().order_by('name')
            groups_data = [
                {
                    'id': group.id,
                    'name': group.name,
                    'users_count': group.user_set.count()
                }
                for group in groups
            ]
            
            return Response({
                'status': 'success',
                'data': groups_data
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error al obtener grupos: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

