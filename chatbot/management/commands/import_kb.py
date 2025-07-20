import json
from django.core.management.base import BaseCommand, CommandError
from chatbot.models import ChatbotCategory, ChatbotKnowledgeBase

class Command(BaseCommand):
    help = 'Importa la base de conocimiento del chatbot desde un archivo JSON.'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='La ruta al archivo JSON que contiene los datos.')

    def handle(self, *args, **options):
        json_file_path = options['json_file']
        self.stdout.write(self.style.SUCCESS(f'Iniciando importación desde {json_file_path}'))

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'El archivo "{json_file_path}" no fue encontrado.')
        except json.JSONDecodeError:
            raise CommandError(f'Error al decodificar el JSON. Asegúrate de que el archivo tiene un formato válido.')

        created_count = 0
        updated_count = 0

        for entry in data:
            category_name = entry.get('category')
            question = entry.get('question')
            answer = entry.get('answer')
            keywords = entry.get('keywords', '')
            is_active = entry.get('is_active', True)

            if not all([category_name, question, answer]):
                self.stderr.write(self.style.WARNING(f'Omitiendo entrada por falta de datos: {entry}'))
                continue

            category, created = ChatbotCategory.objects.get_or_create(
                name=category_name,
                defaults={'description': f'Categoría para {category_name}'}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Categoría creada: "{category_name}"'))

            obj, created = ChatbotKnowledgeBase.objects.update_or_create(
                question=question,
                defaults={
                    'category': category,
                    'answer': answer,
                    'keywords': keywords,
                    'is_active': is_active
                }
            )

            if created:
                created_count += 1
            else:
                updated_count += 1
        
        self.stdout.write(self.style.SUCCESS('--- Importación Finalizada ---'))
        self.stdout.write(self.style.SUCCESS(f'{created_count} entradas creadas.'))
        self.stdout.write(self.style.SUCCESS(f'{updated_count} entradas actualizadas.')) 