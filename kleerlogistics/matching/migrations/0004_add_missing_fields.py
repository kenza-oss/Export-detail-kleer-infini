# Generated manually to add missing timestamp fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matching', '0003_add_price_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='matchingpreferences',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='matchingpreferences',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
