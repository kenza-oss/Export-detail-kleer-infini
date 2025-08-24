# Generated manually to avoid conflicts with existing fields

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('matching', '0001_initial'),
    ]

    operations = [
        # Add new fields to Match model
        migrations.AddField(
            model_name='match',
            name='traveler_earnings',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Gains du voyageur (70-80% du prix total)',
                max_digits=10,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='match',
            name='commission_amount',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Commission de la plateforme (20-30% du prix total)',
                max_digits=10,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='match',
            name='packaging_fee',
            field=models.DecimalField(
                decimal_places=2,
                default=0.0,
                help_text='Frais d\'emballage (500-1000 DA)',
                max_digits=10
            ),
        ),
        migrations.AddField(
            model_name='match',
            name='service_fee',
            field=models.DecimalField(
                decimal_places=2,
                default=0.0,
                help_text='Frais de service',
                max_digits=10
            ),
        ),
        migrations.AddField(
            model_name='match',
            name='accepted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='match',
            name='rejected_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='match',
            name='delivery_otp',
            field=models.CharField(
                blank=True,
                help_text='Code OTP de livraison généré automatiquement',
                max_length=6,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='match',
            name='otp_generated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='match',
            name='otp_expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='match',
            name='delivery_confirmed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='match',
            name='delivery_confirmed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='match',
            name='chat_activated',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='match',
            name='chat_room_id',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='match',
            name='chat_activated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='match',
            name='auto_accepted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='match',
            name='auto_accept_threshold',
            field=models.DecimalField(
                decimal_places=2,
                default=90.0,
                help_text='Seuil de score pour auto-acceptance',
                max_digits=5
            ),
        ),
        migrations.AddField(
            model_name='match',
            name='notification_sent',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='match',
            name='notification_sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        
        # Create MatchingRule model
        migrations.CreateModel(
            name='MatchingRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('min_compatibility_score', models.DecimalField(decimal_places=2, default=30.0, max_digits=5)),
                ('max_distance_km', models.PositiveIntegerField(default=100)),
                ('max_date_flexibility_days', models.PositiveIntegerField(default=7)),
                ('geographic_weight', models.DecimalField(decimal_places=2, default=35.0, max_digits=5)),
                ('weight_weight', models.DecimalField(decimal_places=2, default=20.0, max_digits=5)),
                ('package_type_weight', models.DecimalField(decimal_places=2, default=15.0, max_digits=5)),
                ('fragility_weight', models.DecimalField(decimal_places=2, default=10.0, max_digits=5)),
                ('date_weight', models.DecimalField(decimal_places=2, default=15.0, max_digits=5)),
                ('reputation_weight', models.DecimalField(decimal_places=2, default=5.0, max_digits=5)),
                ('enable_auto_acceptance', models.BooleanField(default=False)),
                ('auto_accept_threshold', models.DecimalField(decimal_places=2, default=90.0, max_digits=5)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Règle de matching',
                'verbose_name_plural': 'Règles de matching',
            },
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='match',
            index=models.Index(fields=['delivery_otp'], name='matching_ma_deliver_ce783e_idx'),
        ),
        migrations.AddIndex(
            model_name='match',
            index=models.Index(fields=['chat_room_id'], name='matching_ma_chat_ro_f79007_idx'),
        ),
    ]
