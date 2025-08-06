# Generated manually for adding active and dieta fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('almuerzos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='almuerzo',
            name='active',
            field=models.BooleanField(default=True, help_text='Indica si el almuerzo está activo y disponible', verbose_name='Activo'),
        ),
        migrations.AddField(
            model_name='almuerzo',
            name='dieta',
            field=models.CharField(blank=True, help_text='Menú especial de dieta (opcional)', max_length=100, null=True, verbose_name='Dieta'),
        ),
    ]