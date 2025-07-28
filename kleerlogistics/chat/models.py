from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Conversation(models.Model):
    """Modèle pour les conversations entre expéditeurs et voyageurs."""
    
    # Relations
    shipment = models.ForeignKey('shipments.Shipment', on_delete=models.CASCADE, related_name='conversations')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_as_sender')
    traveler = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_as_traveler')
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-last_message_at']
        indexes = [
            models.Index(fields=['shipment']),
            models.Index(fields=['sender', 'traveler']),
            models.Index(fields=['is_active']),
        ]
        unique_together = ['shipment', 'sender', 'traveler']
    
    def __str__(self):
        return f"Conversation {self.id} - Shipment {self.shipment.tracking_number}"
    
    @property
    def unread_count_for_user(self, user):
        """Retourne le nombre de messages non lus pour un utilisateur."""
        return self.messages.filter(
            sender__in=[self.sender, self.traveler],
            sender__ne=user,
            is_read=False
        ).count()
    
    def get_other_participant(self, user):
        """Retourne l'autre participant de la conversation."""
        if user == self.sender:
            return self.traveler
        elif user == self.traveler:
            return self.sender
        return None
    
    def mark_as_read_for_user(self, user):
        """Marque tous les messages comme lus pour un utilisateur."""
        self.messages.filter(
            sender__in=[self.sender, self.traveler],
            sender__ne=user,
            is_read=False
        ).update(is_read=True)


class Message(models.Model):
    """Modèle pour les messages dans les conversations."""
    
    MESSAGE_TYPES = [
        ('text', 'Texte'),
        ('image', 'Image'),
        ('file', 'Fichier'),
        ('location', 'Localisation'),
        ('system', 'Système'),
    ]
    
    # Relations
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    
    # Contenu
    content = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    metadata = models.JSONField(default=dict)  # Pour les fichiers, images, etc.
    
    # Statut
    is_read = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"Message {self.id} - {self.sender.username} - {self.created_at}"
    
    def save(self, *args, **kwargs):
        # Mettre à jour last_message_at de la conversation
        super().save(*args, **kwargs)
        self.conversation.last_message_at = self.created_at
        self.conversation.save(update_fields=['last_message_at'])
    
    @property
    def is_system_message(self):
        """Vérifie si c'est un message système."""
        return self.message_type == 'system'
    
    @property
    def file_url(self):
        """Retourne l'URL du fichier si c'est un message de type fichier."""
        if self.message_type == 'file' and 'file_url' in self.metadata:
            return self.metadata['file_url']
        return None
    
    @property
    def image_url(self):
        """Retourne l'URL de l'image si c'est un message de type image."""
        if self.message_type == 'image' and 'image_url' in self.metadata:
            return self.metadata['image_url']
        return None
    
    @property
    def location_data(self):
        """Retourne les données de localisation si c'est un message de type location."""
        if self.message_type == 'location' and 'location' in self.metadata:
            return self.metadata['location']
        return None
