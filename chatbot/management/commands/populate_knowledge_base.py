import json
from django.core.management.base import BaseCommand
from chatbot.models import ChatbotCategory, ChatbotKnowledgeBase

# --- Base de Conocimiento Inicial ---
# Aquí definimos las categorías y las preguntas/respuestas para poblar la BD.
# Se pueden añadir más elementos a esta estructura fácilmente.
KNOWLEDGE_DATA = [
    {
        "category": "Información General",
        "items": [
            {
                "question": "¿Quién es Aquanqa?",
                "answer": "Aquanqa es una empresa líder dedicada a la gestión integral y suministro de agua potable. Nuestro compromiso es garantizar un servicio de calidad, sostenible y accesible para toda la comunidad.",
                "keywords": "empresa, aquanqa, nosotros, quienes somos"
            },
            {
                "question": "¿Cuál es el horario de atención al cliente?",
                "answer": "Nuestras oficinas de atención al cliente están abiertas de Lunes a Viernes, de 8:00 AM a 5:30 PM. Para emergencias, nuestra línea telefónica está disponible las 24 horas del día.",
                "keywords": "horario, atención, oficinas, teléfono, contacto"
            },
            {
                "question": "¿Dónde están ubicadas las oficinas de Aquanqa?",
                "answer": "Nuestra oficina principal se encuentra en la Avenida del Agua, 123, Ciudad Hídrica. Puedes encontrar un listado completo de nuestras sucursales en la sección 'Contacto' de nuestro sitio web oficial.",
                "keywords": "dirección, ubicación, oficinas, sucursales, mapa"
            }
        ]
    },
    {
        "category": "Facturación y Pagos",
        "items": [
            {
                "question": "¿Cómo y dónde puedo pagar mi recibo de agua?",
                "answer": "Puedes pagar tu recibo de manera rápida y segura a través de nuestra app móvil, en la sección de pagos de nuestra página web, en ventanillas de bancos autorizados o en agentes afiliados. ¡Elige la opción más cómoda para ti!",
                "keywords": "pagar, pago, recibo, boleta, factura, dónde, cómo"
            },
            {
                "question": "No me llegó mi boleta, ¿qué puedo hacer?",
                "answer": "No te preocupes. Puedes descargar un duplicado de tu recibo ingresando a tu cuenta en nuestro portal en línea o a través de nuestra aplicación móvil. También puedes solicitarlo en cualquiera de nuestras oficinas.",
                "keywords": "recibo, duplicado, no llegó, boleta, perdido"
            },
            {
                "question": "¿Es posible fraccionar una deuda pendiente?",
                "answer": "Sí, entendemos que pueden surgir dificultades. Ofrecemos planes de financiamiento y facilidades de pago. Por favor, acércate a nuestro centro de atención al cliente para que un asesor pueda ofrecerte una solución personalizada.",
                "keywords": "deuda, fraccionar, financiar, plan de pagos, cuotas"
            }
        ]
    },
    {
        "category": "Servicios y Suministro",
        "items": [
            {
                "question": "¿Qué debo hacer si detecto una fuga de agua?",
                "answer": "Tu ayuda es crucial. Si detectas una fuga, por favor repórtala de inmediato a nuestra línea de emergencia 24/7 al número 0-800-12345. Un equipo técnico atenderá la situación a la brevedad posible.",
                "keywords": "fuga, avería, reporte, emergencia, agua rota"
            },
            {
                "question": "No tengo agua en mi casa, ¿cuál puede ser el motivo?",
                "answer": "Lamentamos el inconveniente. Primero, por favor verifica si hay un corte de servicio programado en tu zona visitando la sección 'Alertas de Servicio' de nuestra web. Si no hay avisos, contáctanos por la línea de emergencia para revisar tu caso.",
                "keywords": "corte de agua, sin servicio, suministro, no tengo agua"
            },
            {
                "question": "¿Cómo solicito una nueva conexión de agua potable?",
                "answer": "¡Bienvenido a Aquanqa! Para solicitar una nueva conexión, necesitas presentar una serie de documentos en nuestras oficinas. Puedes encontrar la lista completa de requisitos y formularios en la sección 'Trámites' de nuestro sitio web.",
                "keywords": "nueva conexión, nuevo suministro, instalar agua, requisitos"
            }
        ]
    },
    {
        "category": "Sobre el Chatbot",
        "items": [
            {
                "question": "¿Quién eres tú?",
                "answer": "Soy AquaBot, el asistente virtual de Aquanqa. Estoy aquí para ayudarte a resolver tus consultas sobre nuestros servicios de manera rápida y eficiente, las 24 horas del día.",
                "keywords": "quién eres, chatbot, asistente, bot, ia"
            },
            {
                "question": "¿Qué tipo de preguntas puedes responder?",
                "answer": "Puedo proporcionarte información sobre pagos, trámites, horarios, reportes de averías y mucho más. ¡Mi conocimiento se actualiza constantemente para servirte mejor!",
                "keywords": "ayuda, qué haces, capacidades, funciones, preguntas"
            },
            {
                "question": "¿Eres una persona de verdad?",
                "answer": "Soy un programa de inteligencia artificial avanzado, creado por el equipo de Aquanqa para ofrecerte la mejor atención digital. Aunque no soy humano, ¡me esfuerzo por entenderte como si lo fuera!",
                "keywords": "real, humano, persona, ia, inteligencia artificial"
            }
        ]
    }
]

class Command(BaseCommand):
    help = 'Puebla la base de datos del chatbot con un conjunto inicial de preguntas y respuestas.'

    def handle(self, *args, **options):
        """
        Punto de entrada para el comando. Itera sobre los datos y los crea en la BD.
        Utiliza `update_or_create` para evitar duplicados si se ejecuta varias veces.
        """
        self.stdout.write(self.style.SUCCESS("Iniciando el proceso para poblar la base de conocimiento..."))
        
        items_created_count = 0
        items_updated_count = 0

        for category_data in KNOWLEDGE_DATA:
            # Crea o actualiza la categoría
            category_name = category_data['category']
            category, created = ChatbotCategory.objects.update_or_create(
                name=category_name,
                defaults={'description': f'Preguntas relacionadas con {category_name}'}
            )
            if created:
                self.stdout.write(f"Categoría creada: '{category_name}'")
            
            # Crea o actualiza las preguntas dentro de la categoría
            for item_data in category_data['items']:
                obj, created = ChatbotKnowledgeBase.objects.update_or_create(
                    question=item_data['question'],
                    defaults={
                        'category': category,
                        'answer': item_data['answer'],
                        'keywords': item_data.get('keywords', '')
                    }
                )
                if created:
                    items_created_count += 1
                else:
                    items_updated_count += 1
        
        self.stdout.write(self.style.SUCCESS("\n¡Proceso completado!"))
        self.stdout.write(f" - Preguntas nuevas creadas: {items_created_count}")
        self.stdout.write(f" - Preguntas existentes actualizadas: {items_updated_count}")

        # --- Fase 2: Enlazar Preguntas Recomendadas ---
        self.stdout.write("\nIniciando el enlazado de preguntas recomendadas...")
        
        try:
            # Mapeo de preguntas principales a sus recomendadas
            recommendations_map = {
                "¿Cómo y dónde puedo pagar mi recibo de agua?": [
                    "No me llegó mi boleta, ¿qué puedo hacer?",
                    "¿Es posible fraccionar una deuda pendiente?"
                ],
                "No tengo agua en mi casa, ¿cuál puede ser el motivo?": [
                    "¿Qué debo hacer si detecto una fuga de agua?"
                ],
                "¿Quién eres tú?": [
                    "¿Qué tipo de preguntas puedes responder?",
                    "¿Eres una persona de verdad?"
                ]
            }

            recommendations_linked = 0
            for main_question_str, recommended_strs in recommendations_map.items():
                # Obtener el objeto de la pregunta principal
                main_question_obj = ChatbotKnowledgeBase.objects.get(question=main_question_str)
                
                # Limpiar recomendaciones existentes para evitar duplicados en re-ejecuciones
                main_question_obj.recommended_questions.clear()

                # Obtener los objetos de las preguntas recomendadas y añadirlos
                for rec_str in recommended_strs:
                    rec_obj = ChatbotKnowledgeBase.objects.get(question=rec_str)
                    main_question_obj.recommended_questions.add(rec_obj)
                    recommendations_linked += 1
            
            self.stdout.write(self.style.SUCCESS(f"Se enlazaron {recommendations_linked} preguntas recomendadas."))

        except ChatbotKnowledgeBase.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f"Error: No se pudo encontrar una de las preguntas para enlazar. {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ocurrió un error inesperado al enlazar preguntas: {e}"))


        self.stdout.write(self.style.WARNING("\nIMPORTANTE: No olvides ejecutar 'python manage.py generate_embeddings' para que el chatbot aprenda estas nuevas preguntas.")) 