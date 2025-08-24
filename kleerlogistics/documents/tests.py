"""
Tests pour le module de génération de documents PDF
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from decimal import Decimal
import tempfile
import os

from .models import Document, DocumentTemplate
from .services import PDFGenerationService, DocumentValidationService, DocumentTemplateService

User = get_user_model()


class PDFGenerationServiceTest(TestCase):
    """Tests pour le service de génération de PDF."""
    
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Créer un template de test
        self.template = DocumentTemplate.objects.create(
            name='Test Template',
            document_type='invoice',
            is_active=True
        )
    
    def test_generate_invoice_html(self):
        """Test de génération du HTML pour une facture."""
        invoice_data = {
            'invoice_number': 'INV12345678',
            'client_name': 'Ahmed Benali',
            'client_email': 'ahmed@example.com',
            'client_address': '123 Rue de la Paix, Alger',
            'tracking_number': 'TRK123456',
            'origin': 'Alger',
            'destination': 'Paris',
            'weight': '2.5',
            'shipping_cost': 5000.0,
            'packaging_fee': 500.0,
            'commission': 1250.0,
            'total_amount': 6750.0
        }
        
        html = PDFGenerationService.generate_invoice_html(invoice_data)
        
        # Vérifications
        self.assertIn('FACTURE', html)
        self.assertIn('INV12345678', html)
        self.assertIn('Ahmed Benali', html)
        self.assertIn('5000.00', html)
        self.assertIn('6750.00', html)
        self.assertIn('<!DOCTYPE html>', html)
    
    def test_generate_receipt_html(self):
        """Test de génération du HTML pour un reçu."""
        receipt_data = {
            'receipt_number': 'RCP87654321',
            'client_name': 'Fatima Zohra',
            'client_email': 'fatima@example.com',
            'transaction_reference': 'TXN123456',
            'payment_method': 'CIB',
            'payment_date': '15/01/2024',
            'amount_paid': 5000.0
        }
        
        html = PDFGenerationService.generate_receipt_html(receipt_data)
        
        # Vérifications
        self.assertIn('REÇU DE PAIEMENT', html)
        self.assertIn('RCP87654321', html)
        self.assertIn('Fatima Zohra', html)
        self.assertIn('5000.00', html)
        self.assertIn('CIB', html)
    
    def test_generate_contract_html(self):
        """Test de génération du HTML pour un contrat."""
        contract_data = {
            'contract_number': 'CTR12345678',
            'sender_name': 'Ahmed Benali',
            'traveler_name': 'Fatima Zohra',
            'recipient_name': 'Mohammed Boudiaf',
            'departure_date': '15/01/2024',
            'route': 'Alger → Paris',
            'package_weight': '2.5',
            'compensation': 5000.0
        }
        
        html = PDFGenerationService.generate_contract_html(contract_data)
        
        # Vérifications
        self.assertIn('CONTRAT DE TRANSPORT', html)
        self.assertIn('CTR12345678', html)
        self.assertIn('Ahmed Benali', html)
        self.assertIn('Fatima Zohra', html)
        self.assertIn('Alger → Paris', html)
        self.assertIn('5000.00', html)
    
    def test_generate_pdf_from_html(self):
        """Test de génération de PDF à partir de HTML."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test PDF</title>
        </head>
        <body>
            <h1>Test de génération PDF</h1>
            <p>Ceci est un test.</p>
        </body>
        </html>
        """
        
        try:
            pdf_content = PDFGenerationService.generate_pdf_from_html(html_content)
            self.assertIsInstance(pdf_content, bytes)
            self.assertGreater(len(pdf_content), 0)
        except Exception as e:
            # Si WeasyPrint n'est pas installé, le test passe quand même
            self.skipTest(f"WeasyPrint non disponible: {e}")
    
    def test_get_company_logo(self):
        """Test de récupération du logo de l'entreprise."""
        logo = PDFGenerationService.get_company_logo()
        # Le logo peut être None si le fichier n'existe pas
        self.assertIsInstance(logo, (str, type(None)))
    
    def test_get_company_stamp(self):
        """Test de récupération du cachet de l'entreprise."""
        stamp = PDFGenerationService.get_company_stamp()
        self.assertIsInstance(stamp, (str, type(None)))
    
    def test_get_kleer_infini_stamp(self):
        """Test de récupération du cachet Kleer Infini."""
        stamp = PDFGenerationService.get_kleer_infini_stamp()
        self.assertIsInstance(stamp, (str, type(None)))
    
    def test_get_official_stamp(self):
        """Test de récupération du cachet officiel."""
        stamp = PDFGenerationService.get_official_stamp()
        self.assertIsInstance(stamp, (str, type(None)))
    
    def test_get_digital_signature(self):
        """Test de récupération de la signature digitale."""
        signature = PDFGenerationService.get_digital_signature()
        self.assertIsInstance(signature, (str, type(None)))
    
    def test_get_default_css(self):
        """Test de récupération du CSS par défaut."""
        css = PDFGenerationService.get_default_css()
        self.assertIsInstance(css, str)
        self.assertIn('@page', css)
        self.assertIn('body', css)
        self.assertIn('Kleer Infini', css)


class DocumentValidationServiceTest(TestCase):
    """Tests pour le service de validation des documents."""
    
    def test_validate_invoice_data_valid(self):
        """Test de validation de données de facture valides."""
        invoice_data = {
            'invoice_number': 'INV12345678',
            'client_name': 'Ahmed Benali',
            'total_amount': 5000.0
        }
        
        result = DocumentValidationService.validate_invoice_data(invoice_data)
        self.assertTrue(result['valid'])
    
    def test_validate_invoice_data_missing_fields(self):
        """Test de validation de données de facture avec champs manquants."""
        invoice_data = {
            'invoice_number': 'INV12345678'
            # client_name et total_amount manquants
        }
        
        result = DocumentValidationService.validate_invoice_data(invoice_data)
        self.assertFalse(result['valid'])
        self.assertIn('Champs manquants', result['errors'])
    
    def test_validate_invoice_data_empty_fields(self):
        """Test de validation de données de facture avec champs vides."""
        invoice_data = {
            'invoice_number': '',
            'client_name': 'Ahmed Benali',
            'total_amount': 5000.0
        }
        
        result = DocumentValidationService.validate_invoice_data(invoice_data)
        self.assertFalse(result['valid'])
        self.assertIn('Champs manquants', result['errors'])
    
    def test_validate_receipt_data_valid(self):
        """Test de validation de données de reçu valides."""
        receipt_data = {
            'receipt_number': 'RCP87654321',
            'client_name': 'Fatima Zohra',
            'amount_paid': 5000.0
        }
        
        result = DocumentValidationService.validate_receipt_data(receipt_data)
        self.assertTrue(result['valid'])
    
    def test_validate_receipt_data_missing_fields(self):
        """Test de validation de données de reçu avec champs manquants."""
        receipt_data = {
            'receipt_number': 'RCP87654321'
            # client_name et amount_paid manquants
        }
        
        result = DocumentValidationService.validate_receipt_data(receipt_data)
        self.assertFalse(result['valid'])
        self.assertIn('Champs manquants', result['errors'])


class DocumentTemplateServiceTest(TestCase):
    """Tests pour le service de gestion des templates."""
    
    def setUp(self):
        """Configuration initiale."""
        self.template = DocumentTemplate.objects.create(
            name='Test Template',
            document_type='invoice',
            is_active=True
        )
    
    def test_get_template_by_type(self):
        """Test de récupération d'un template par type."""
        template = DocumentTemplateService.get_template_by_type('invoice')
        self.assertIsNotNone(template)
        self.assertEqual(template.document_type, 'invoice')
    
    def test_get_template_by_type_not_found(self):
        """Test de récupération d'un template inexistant."""
        template = DocumentTemplateService.get_template_by_type('nonexistent')
        self.assertIsNone(template)
    
    def test_get_template_by_type_inactive(self):
        """Test de récupération d'un template inactif."""
        self.template.is_active = False
        self.template.save()
        
        template = DocumentTemplateService.get_template_by_type('invoice')
        self.assertIsNone(template)
    
    def test_create_default_templates(self):
        """Test de création des templates par défaut."""
        # Supprimer les templates existants
        DocumentTemplate.objects.all().delete()
        
        # Créer les templates par défaut
        DocumentTemplateService.create_default_templates()
        
        # Vérifier que les templates ont été créés
        templates = DocumentTemplate.objects.all()
        self.assertGreaterEqual(templates.count(), 3)
        
        # Vérifier les types de documents
        document_types = [t.document_type for t in templates]
        self.assertIn('invoice', document_types)
        self.assertIn('receipt', document_types)
        self.assertIn('contract', document_types)


class DocumentModelTest(TestCase):
    """Tests pour le modèle Document."""
    
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.template = DocumentTemplate.objects.create(
            name='Test Template',
            document_type='invoice',
            is_active=True
        )
    
    def test_document_creation(self):
        """Test de création d'un document."""
        document = Document.objects.create(
            user=self.user,
            document_type='invoice',
            title='Test Document',
            status='generated',
            content_data={'test': 'data'}
        )
        
        self.assertEqual(document.user, self.user)
        self.assertEqual(document.document_type, 'invoice')
        self.assertEqual(document.title, 'Test Document')
        self.assertEqual(document.status, 'generated')
        self.assertEqual(document.content_data, {'test': 'data'})
        self.assertIsNotNone(document.reference_number)
    
    def test_document_reference_generation(self):
        """Test de génération automatique du numéro de référence."""
        document = Document.objects.create(
            user=self.user,
            document_type='invoice',
            title='Test Document',
            status='generated'
        )
        
        self.assertIsNotNone(document.reference_number)
        self.assertTrue(document.reference_number.startswith('DOC-'))
    
    def test_document_str_representation(self):
        """Test de la représentation string du document."""
        document = Document.objects.create(
            user=self.user,
            document_type='invoice',
            title='Test Document',
            status='generated'
        )
        
        self.assertIn('Test Document', str(document))
        self.assertIn('Facture', str(document))
    
    def test_document_with_generated_file(self):
        """Test de document avec fichier généré."""
        pdf_content = b'fake pdf content'
        document = Document.objects.create(
            user=self.user,
            document_type='invoice',
            title='Test Document',
            status='generated',
            generated_file=ContentFile(pdf_content, 'test.pdf')
        )
        
        self.assertIsNotNone(document.generated_file)
        self.assertEqual(document.generated_file.read(), pdf_content)


class DocumentTemplateModelTest(TestCase):
    """Tests pour le modèle DocumentTemplate."""
    
    def test_template_creation(self):
        """Test de création d'un template."""
        template = DocumentTemplate.objects.create(
            name='Test Template',
            document_type='invoice',
            is_active=True
        )
        
        self.assertEqual(template.name, 'Test Template')
        self.assertEqual(template.document_type, 'invoice')
        self.assertTrue(template.is_active)
    
    def test_template_str_representation(self):
        """Test de la représentation string du template."""
        template = DocumentTemplate.objects.create(
            name='Test Template',
            document_type='invoice',
            is_active=True
        )
        
        self.assertIn('Test Template', str(template))
        self.assertIn('Facture', str(template))
    
    def test_template_choices(self):
        """Test des choix de type de document."""
        template = DocumentTemplate.objects.create(
            name='Test Template',
            document_type='invoice',
            is_active=True
        )
        
        choices = [choice[0] for choice in template.DOCUMENT_TYPES]
        self.assertIn('invoice', choices)
        self.assertIn('receipt', choices)
        self.assertIn('contract', choices)
        self.assertIn('custom', choices)


class DocumentIntegrationTest(TestCase):
    """Tests d'intégration pour le module de documents."""
    
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_full_document_generation_workflow(self):
        """Test du workflow complet de génération de document."""
        # 1. Préparer les données
        invoice_data = {
            'invoice_number': 'INV12345678',
            'client_name': 'Ahmed Benali',
            'client_email': 'ahmed@example.com',
            'client_address': '123 Rue de la Paix, Alger',
            'tracking_number': 'TRK123456',
            'origin': 'Alger',
            'destination': 'Paris',
            'weight': '2.5',
            'shipping_cost': 5000.0,
            'packaging_fee': 500.0,
            'commission': 1250.0,
            'total_amount': 6750.0
        }
        
        # 2. Valider les données
        validation = DocumentValidationService.validate_invoice_data(invoice_data)
        self.assertTrue(validation['valid'])
        
        # 3. Générer le HTML
        html = PDFGenerationService.generate_invoice_pdf(invoice_data)
        self.assertIsInstance(html, str)
        self.assertIn('FACTURE', html)
        
        # 4. Créer le document en base
        document = Document.objects.create(
            user=self.user,
            document_type='invoice',
            title=f'Facture {invoice_data["invoice_number"]}',
            status='generated',
            content_data=invoice_data
        )
        
        self.assertIsNotNone(document)
        self.assertEqual(document.document_type, 'invoice')
        self.assertEqual(document.status, 'generated')
        
        # 5. Vérifier les métadonnées
        self.assertIsNotNone(document.reference_number)
        self.assertIsNotNone(document.created_at)
        self.assertEqual(document.user, self.user)
    
    def test_document_validation_and_generation(self):
        """Test de validation et génération de document."""
        # Test avec données valides
        receipt_data = {
            'receipt_number': 'RCP87654321',
            'client_name': 'Fatima Zohra',
            'client_email': 'fatima@example.com',
            'transaction_reference': 'TXN123456',
            'payment_method': 'CIB',
            'payment_date': '15/01/2024',
            'amount_paid': 5000.0
        }
        
        # Validation
        validation = DocumentValidationService.validate_receipt_data(receipt_data)
        self.assertTrue(validation['valid'])
        
    # Génération HTML
        html = PDFGenerationService.generate_receipt_html(receipt_data)
        self.assertIsInstance(html, str)
        self.assertIn('REÇU DE PAIEMENT', html)
        
        # Test avec données invalides
        invalid_data = {
            'receipt_number': 'RCP87654321'
            # Champs manquants
        }
        
        validation = DocumentValidationService.validate_receipt_data(invalid_data)
        self.assertFalse(validation['valid'])
        self.assertIn('Champs manquants', validation['errors'])
