# Generated manually to add missing fields to MatchingPreferences

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matching', '0004_add_missing_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='matchingpreferences',
            name='accepts_fragile',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='matchingpreferences',
            name='accepts_urgent',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='matchingpreferences',
            name='max_distance_km',
            field=models.PositiveIntegerField(default=100),
        ),
        migrations.AddField(
            model_name='matchingpreferences',
            name='max_price_per_kg',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='matchingpreferences',
            name='preferred_package_types',
            field=models.JSONField(default=list),
        ),
    ]
