# Generated manually to add missing price fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matching', '0002_add_matching_features'),
    ]

    operations = [
        migrations.AddField(
            model_name='matchingpreferences',
            name='min_price',
            field=models.DecimalField(
                max_digits=10, 
                decimal_places=2, 
                null=True, 
                blank=True,
                help_text='Prix minimum accepté'
            ),
        ),
        migrations.AddField(
            model_name='matchingpreferences',
            name='max_price',
            field=models.DecimalField(
                max_digits=10, 
                decimal_places=2, 
                null=True, 
                blank=True,
                help_text='Prix maximum accepté'
            ),
        ),
    ]
