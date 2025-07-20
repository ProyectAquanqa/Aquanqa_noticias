from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile
from core.admin import AuditModelAdmin

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'perfiles'
    # Especificamos cuál es la clave foránea principal hacia User,
    # ya que el modelo Profile ahora tiene 3 (user, created_by, updated_by).
    fk_name = 'user'
    readonly_fields = ('created_by', 'updated_by')

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

# Anulamos el registro del UserAdmin base y registramos el nuestro
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Profile)
class ProfileAdmin(AuditModelAdmin):
    list_display = ('user', 'created_at', 'updated_at', 'created_by', 'updated_by')
    readonly_fields = ('user', 'created_by', 'updated_by')
