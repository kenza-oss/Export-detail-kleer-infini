"""
Models for documents app - PDF document generation
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class DocumentTemplate(models.Model):
    """Modèle pour les templates de documents."""
    
    DOCUMENT_TYPES = [
        ('invoice', 'Facture'),
        ('receipt', 'Reçu'),
        ('contract', 'Contrat'),
        ('custom', 'Document personnalisé'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Nom du template")
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, verbose_name="Type de document")
    template_file = models.FileField(upload_to='document_templates/', verbose_name="Fichier template")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Template de document"
        verbose_name_plural = "Templates de documents"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_document_type_display()})"

class Document(models.Model):
    """Modèle pour les documents générés."""
    
    DOCUMENT_TYPES = [
        ('invoice', 'Facture'),
        ('receipt', 'Reçu'),
        ('contract', 'Contrat'),
        ('custom', 'Document personnalisé'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('generated', 'Généré'),
        ('sent', 'Envoyé'),
        ('archived', 'Archivé'),
    ]
    
    # Informations de base
    document_id = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name="ID du document")
    title = models.CharField(max_length=200, verbose_name="Titre")
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, verbose_name="Type de document")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Statut")
    
    # Relations
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    template = models.ForeignKey(DocumentTemplate, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Template")
    
    # Contenu et données
    content_data = models.JSONField(default=dict, verbose_name="Données du contenu")
    generated_file = models.FileField(upload_to='generated_documents/', null=True, blank=True, verbose_name="Fichier généré")
    
    # Métadonnées
    reference_number = models.CharField(max_length=50, unique=True, verbose_name="Numéro de référence")
    description = models.TextField(blank=True, verbose_name="Description")
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    generated_at = models.DateTimeField(null=True, blank=True, verbose_name="Généré le")
    
    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_document_type_display()})"
    
    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = f"DOC-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def generate_reference(self):
        """Générer un numéro de référence unique."""
        if not self.reference_number:
            self.reference_number = f"DOC-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
            self.save()
        return self.reference_number

class Invoice(models.Model):
    """Modèle pour les factures."""
    
    document = models.OneToOneField(Document, on_delete=models.CASCADE, verbose_name="Document")
    
    # Informations client
    client_name = models.CharField(max_length=200, verbose_name="Nom du client")
    client_email = models.EmailField(verbose_name="Email du client")
    client_address = models.TextField(verbose_name="Adresse du client")
    
    # Informations de facturation
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name="Numéro de facture")
    issue_date = models.DateField(verbose_name="Date d'émission")
    due_date = models.DateField(verbose_name="Date d'échéance")
    
    # Montants
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sous-total")
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Montant des taxes")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant total")
    
    # Statut
    is_paid = models.BooleanField(default=False, verbose_name="Payée")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Payée le")
    
    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
    
    def __str__(self):
        return f"Facture {self.invoice_number} - {self.client_name}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

class Receipt(models.Model):
    """Modèle pour les reçus."""
    
    document = models.OneToOneField(Document, on_delete=models.CASCADE, verbose_name="Document")
    
    # Informations client
    client_name = models.CharField(max_length=200, verbose_name="Nom du client")
    client_email = models.EmailField(verbose_name="Email du client")
    
    # Informations de paiement
    receipt_number = models.CharField(max_length=50, unique=True, verbose_name="Numéro de reçu")
    payment_date = models.DateTimeField(verbose_name="Date de paiement")
    payment_method = models.CharField(max_length=50, verbose_name="Méthode de paiement")
    
    # Montants
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant payé")
    transaction_id = models.CharField(max_length=100, blank=True, verbose_name="ID de transaction")
    
    class Meta:
        verbose_name = "Reçu"
        verbose_name_plural = "Reçus"
    
    def __str__(self):
        return f"Reçu {self.receipt_number} - {self.client_name}"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = f"REC-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
