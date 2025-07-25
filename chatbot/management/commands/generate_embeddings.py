from django.core.management.base import BaseCommand
from django.db.models import F
from chatbot.models import ChatbotKnowledgeBase
from sentence_transformers import SentenceTransformer
import torch

class Command(BaseCommand):
    help = 'Genera y guarda los embeddings para las preguntas de la base de conocimiento del chatbot.'

    def handle(self, *args, **options):
        """
        El punto de entrada principal para el comando de Django.
        Carga el modelo, procesa las preguntas y guarda los embeddings.
        """
        self.stdout.write("Iniciando la generación de embeddings para el chatbot...")

        # Determinar el dispositivo a usar (GPU si está disponible, si no CPU)
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.stdout.write(f"Usando dispositivo: {device}")

        try:
            # Cargar un modelo de transformador de frases pre-entrenado para español.
            # Este modelo es excelente para tareas de similitud de texto.
            # La primera vez que se ejecute, descargará el modelo (puede tardar).
            model = SentenceTransformer('hiiamsid/sentence_similarity_spanish_es', device=device)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error al cargar el modelo de SentenceTransformer: {e}"))
            return

        # Obtener todas las preguntas de la base de conocimiento que necesitan un embedding.
        knowledge_base = ChatbotKnowledgeBase.objects.all()
        questions_to_process = [item.question for item in knowledge_base]

        if not questions_to_process:
            self.stdout.write(self.style.WARNING("No hay preguntas en la base de conocimiento para procesar."))
            return

        self.stdout.write(f"Codificando {len(questions_to_process)} preguntas. Esto puede tardar un momento...")

        try:
            # Convertir todas las preguntas a embeddings.
            # La librería procesa esto en un lote (batch), lo cual es muy eficiente.
            embeddings = model.encode(questions_to_process, show_progress_bar=True)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error durante la codificación de las preguntas: {e}"))
            return

        # Guardar cada embedding en su objeto correspondiente en la base de datos.
        self.stdout.write("Guardando los embeddings en la base de datos...")
        for i, item in enumerate(knowledge_base):
            # El embedding se convierte a una lista de Python para ser compatible con el JSONField.
            item.question_embedding = embeddings[i].tolist()
            item.save(update_fields=['question_embedding'])

        self.stdout.write(self.style.SUCCESS(f"¡Proceso completado! Se han generado y guardado {len(knowledge_base)} embeddings.")) 