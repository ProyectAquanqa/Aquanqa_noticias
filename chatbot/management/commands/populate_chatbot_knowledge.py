from django.core.management.base import BaseCommand
from django.db import transaction
from chatbot.models import ChatbotCategory, ChatbotKnowledgeBase
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Populate the chatbot knowledge base with initial data.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting to populate chatbot knowledge base...'))
        
        # Obtener un superusuario para los campos de auditoría.
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('No superuser found. Please create one before running this command.'))
            return

        # --- Definición de Datos ---
        knowledge_data = {
            "Información General": {
                "description": "Respuestas a preguntas comunes y generales sobre la empresa.",
                "entries": [
                    {
                        "question": "¿Cuál es el horario de atención?",
                        "answer": "Nuestro horario de atención es de lunes a viernes, de 9:00 AM a 6:00 PM.",
                        "keywords": "horario, atención, oficina, horas, laboral",
                        "is_recommended": True
                    },
                    {
                        "question": "¿Dónde están ubicadas sus oficinas?",
                        "answer": "Nuestras oficinas principales se encuentran en Av. Principal 123, Ciudad Capital.",
                        "keywords": "dirección, ubicación, mapa, llegar, sede"
                    }
                ]
            },
            "Recursos Humanos": {
                "description": "Información sobre políticas de RRHH, beneficios y cultura.",
                "entries": [
                    {
                        "question": "¿Cuáles son los beneficios para empleados?",
                        "answer": "Ofrecemos un paquete completo de beneficios que incluye seguro médico, seguro dental, 20 días de vacaciones al año y un plan de desarrollo profesional.",
                        "keywords": "beneficios, seguro, vacaciones, desarrollo, perks",
                        "is_recommended": True
                    },
                    {
                        "question": "¿Cómo es la política de trabajo remoto?",
                        "answer": "Tenemos una política de trabajo híbrida. Los empleados pueden trabajar desde casa hasta 3 días a la semana, coordinando con su equipo.",
                        "keywords": "remoto, teletrabajo, casa, híbrido, política"
                    }
                ]
            },
            "Soporte Técnico": {
                "description": "Ayuda con problemas técnicos comunes.",
                "entries": [
                    {
                        "question": "No puedo acceder a mi cuenta, ¿qué hago?",
                        "answer": "Si no puedes acceder, intenta restablecer tu contraseña usando el enlace 'Olvidé mi contraseña' en la página de inicio de sesión. Si el problema persiste, contacta a soporte técnico.",
                        "keywords": "acceso, contraseña, login, cuenta, problema",
                        "is_recommended": True
                    },
                    {
                        "question": "La aplicación va lenta, ¿cómo puedo solucionarlo?",
                        "answer": "Para mejorar el rendimiento, intenta borrar la caché de la aplicación o reiniciarla. Asegúrate también de tener la última versión instalada.",
                        "keywords": "lento, rendimiento, velocidad, optimizar, app"
                    }
                ]
            }
        }

        # --- Proceso de Carga ---
        for category_name, data in knowledge_data.items():
            # Crear o actualizar categoría
            category, created = ChatbotCategory.objects.update_or_create(
                name=category_name,
                defaults={
                    'description': data['description'],
                    'created_by': admin_user,
                    'updated_by': admin_user
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Category "{category_name}" created.'))
            else:
                self.stdout.write(self.style.WARNING(f'Category "{category_name}" already exists. Updating...'))

            # Crear entradas de conocimiento para la categoría
            for entry_data in data['entries']:
                _, created = ChatbotKnowledgeBase.objects.update_or_create(
                    question=entry_data['question'],
                    defaults={
                        'category': category,
                        'answer': entry_data['answer'],
                        'keywords': entry_data['keywords'],
                        'is_active': True,
                        'is_recommended': entry_data.get('is_recommended', False),
                        'created_by': admin_user,
                        'updated_by': admin_user
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f'  - Knowledge entry "{entry_data["question"]}" added.'))

        self.stdout.write(self.style.SUCCESS('Finished populating chatbot knowledge base.')) 