# Generated by Django 5.2.4 on 2025-07-24 13:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0004_remove_chatbotknowledgebase_is_recommended_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatbotknowledgebase',
            name='view_count',
            field=models.PositiveIntegerField(db_index=True, default=0, help_text='Contador de cuántas veces se ha mostrado esta respuesta.'),
        ),
        migrations.AlterField(
            model_name='chatbotknowledgebase',
            name='recommended_questions',
            field=models.ManyToManyField(blank=True, help_text='Selecciona otras preguntas para sugerir después de esta respuesta.', to='chatbot.chatbotknowledgebase', verbose_name='Preguntas Recomendadas'),
        ),
    ]
