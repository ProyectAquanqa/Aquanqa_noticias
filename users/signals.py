from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile

# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     """
#     DEPRECADO: La creación de perfiles ahora se maneja en el serializador
#     para poder asignar correctamente el 'created_by'.
#     """
#     if created:
#         Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Esta señal sigue siendo útil para guardar el perfil cuando el usuario se guarda.
    # Por ejemplo, si se actualiza el email o el nombre desde el admin de Django.
    if hasattr(instance, 'profile'):
        instance.profile.save() 