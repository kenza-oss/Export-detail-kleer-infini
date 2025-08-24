from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.cache import cache
import json

User = get_user_model()

class TranslationCategory(models.Model):
    """
    Catégories de traductions pour organiser les contenus
    """
    name = models.CharField(_('Nom'), max_length=100)
    code = models.CharField(_('Code'), max_length=50, unique=True)
    description = models.TextField(_('Description'), blank=True)
    is_active = models.BooleanField(_('Actif'), default=True)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('Catégorie de traduction')
        verbose_name_plural = _('Catégories de traduction')
        ordering = ['name']

    def __str__(self):
        return self.name

class TranslationKey(models.Model):
    """
    Clés de traduction pour identifier les textes à traduire
    """
    key = models.CharField(_('Clé'), max_length=200, unique=True)
    category = models.ForeignKey(
        TranslationCategory, 
        on_delete=models.CASCADE, 
        related_name='translation_keys',
        verbose_name=_('Catégorie')
    )
    description = models.TextField(_('Description'), blank=True)
    context = models.TextField(_('Contexte'), blank=True, help_text=_('Contexte d\'utilisation de cette traduction'))
    is_active = models.BooleanField(_('Actif'), default=True)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('Clé de traduction')
        verbose_name_plural = _('Clés de traduction')
        ordering = ['key']

    def __str__(self):
        return self.key

    def get_translation(self, language_code):
        """Récupère la traduction pour une langue donnée"""
        try:
            return self.translations.get(language_code=language_code).text
        except Translation.DoesNotExist:
            return self.key

class Translation(models.Model):
    """
    Traductions pour chaque clé et langue
    """
    LANGUAGE_CHOICES = [
        ('fr', 'Français'),
        ('en', 'English'),
        ('ar', 'العربية'),
    ]

    key = models.ForeignKey(
        TranslationKey, 
        on_delete=models.CASCADE, 
        related_name='translations',
        verbose_name=_('Clé')
    )
    language_code = models.CharField(_('Code langue'), max_length=2, choices=LANGUAGE_CHOICES)
    text = models.TextField(_('Texte traduit'))
    is_approved = models.BooleanField(_('Approuvé'), default=False)
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_translations',
        verbose_name=_('Approuvé par')
    )
    approved_at = models.DateTimeField(_('Approuvé le'), null=True, blank=True)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('Traduction')
        verbose_name_plural = _('Traductions')
        unique_together = ['key', 'language_code']
        ordering = ['key__key', 'language_code']

    def __str__(self):
        return f"{self.key.key} ({self.language_code})"

    def save(self, *args, **kwargs):
        # Invalider le cache lors de la sauvegarde
        cache_key = f"translation_{self.key.key}_{self.language_code}"
        cache.delete(cache_key)
        super().save(*args, **kwargs)

class UserLanguagePreference(models.Model):
    """
    Préférences de langue des utilisateurs
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='language_preference',
        verbose_name=_('Utilisateur')
    )
    preferred_language = models.CharField(
        _('Langue préférée'), 
        max_length=2, 
        choices=Translation.LANGUAGE_CHOICES,
        default='fr'
    )
    fallback_language = models.CharField(
        _('Langue de secours'), 
        max_length=2, 
        choices=Translation.LANGUAGE_CHOICES,
        default='en'
    )
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('Préférence de langue')
        verbose_name_plural = _('Préférences de langue')

    def __str__(self):
        return f"{self.user.username} - {self.preferred_language}"

class TranslationTemplate(models.Model):
    """
    Modèles de traduction pour les emails, notifications, etc.
    """
    TEMPLATE_TYPES = [
        ('email', _('Email')),
        ('sms', _('SMS')),
        ('notification', _('Notification')),
        ('document', _('Document')),
        ('ui', _('Interface utilisateur')),
    ]

    name = models.CharField(_('Nom'), max_length=100)
    template_type = models.CharField(_('Type'), max_length=20, choices=TEMPLATE_TYPES)
    key = models.CharField(_('Clé'), max_length=200, unique=True)
    variables = models.JSONField(_('Variables'), default=list, help_text=_('Liste des variables disponibles'))
    category = models.ForeignKey(
        TranslationCategory, 
        on_delete=models.CASCADE, 
        related_name='templates',
        verbose_name=_('Catégorie')
    )
    is_active = models.BooleanField(_('Actif'), default=True)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('Modèle de traduction')
        verbose_name_plural = _('Modèles de traduction')
        ordering = ['name']

    def __str__(self):
        return self.name

class TranslationTemplateContent(models.Model):
    """
    Contenu des modèles de traduction par langue
    """
    template = models.ForeignKey(
        TranslationTemplate, 
        on_delete=models.CASCADE, 
        related_name='contents',
        verbose_name=_('Modèle')
    )
    language_code = models.CharField(_('Code langue'), max_length=2, choices=Translation.LANGUAGE_CHOICES)
    subject = models.CharField(_('Sujet'), max_length=200, blank=True)
    content = models.TextField(_('Contenu'))
    is_approved = models.BooleanField(_('Approuvé'), default=False)
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_template_contents',
        verbose_name=_('Approuvé par')
    )
    approved_at = models.DateTimeField(_('Approuvé le'), null=True, blank=True)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)

    class Meta:
        verbose_name = _('Contenu de modèle')
        verbose_name_plural = _('Contenus de modèles')
        unique_together = ['template', 'language_code']
        ordering = ['template__name', 'language_code']

    def __str__(self):
        return f"{self.template.name} ({self.language_code})"

class TranslationCache(models.Model):
    """
    Cache des traductions pour optimiser les performances
    """
    cache_key = models.CharField(_('Clé de cache'), max_length=255, unique=True)
    language_code = models.CharField(_('Code langue'), max_length=2)
    content = models.TextField(_('Contenu'))
    expires_at = models.DateTimeField(_('Expire le'))
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)

    class Meta:
        verbose_name = _('Cache de traduction')
        verbose_name_plural = _('Caches de traduction')
        indexes = [
            models.Index(fields=['cache_key', 'language_code']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.cache_key} ({self.language_code})"

    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
