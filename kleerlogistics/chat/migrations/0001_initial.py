# Generated manually for chat app

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('shipments', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_message_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conversations_as_sender', to='users.user')),
                ('shipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conversations', to='shipments.shipment')),
                ('traveler', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conversations_as_traveler', to='users.user')),
            ],
            options={
                'ordering': ['-last_message_at'],
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('message_type', models.CharField(choices=[('text', 'Texte'), ('image', 'Image'), ('file', 'Fichier'), ('location', 'Localisation'), ('system', 'Système')], default='text', max_length=20)),
                ('metadata', models.JSONField(default=dict)),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='chat.conversation')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to='users.user')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='conversation',
            index=models.Index(fields=['shipment'], name='chat_convers_shipmen_123456'),
        ),
        migrations.AddIndex(
            model_name='conversation',
            index=models.Index(fields=['sender', 'traveler'], name='chat_convers_sender__123456'),
        ),
        migrations.AddIndex(
            model_name='conversation',
            index=models.Index(fields=['is_active'], name='chat_convers_is_acti_123456'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['conversation', 'created_at'], name='chat_message_convers_123456'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['sender'], name='chat_message_sender_123456'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['is_read'], name='chat_message_is_read_123456'),
        ),
        migrations.AlterUniqueTogether(
            name='conversation',
            unique_together={('shipment', 'sender', 'traveler')},
        ),
    ] 