"""
Services pour la génération de documents PDF avec WeasyPrint
Support pour cachet, logo et signature
"""

import os
import io
import base64
from datetime import datetime
from django.conf import settings
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.utils import timezone
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import logging

logger = logging.getLogger(__name__)


class PDFGenerationService:
    """Service pour la génération de documents PDF avec WeasyPrint."""
    
    @staticmethod
    def generate_invoice_pdf(invoice_data):
        """
        Générer une facture PDF avec cachet et logo.
        
        Args:
            invoice_data: Données de la facture
            
        Returns:
            bytes: Contenu PDF
        """
        try:
            # Générer le HTML programmatiquement
            html_content = PDFGenerationService.generate_invoice_html(invoice_data)
            
            # Générer le PDF avec WeasyPrint
            pdf_content = PDFGenerationService.generate_pdf_from_html(html_content)
            
            logger.info(f"Facture PDF générée: {invoice_data.get('invoice_number', 'N/A')}")
            return pdf_content
            
        except Exception as e:
            logger.error(f"Erreur génération facture PDF: {str(e)}")
            raise
    
    @staticmethod
    def generate_receipt_pdf(receipt_data):
        """
        Générer un reçu PDF avec cachet et signature.
        
        Args:
            receipt_data: Données du reçu
            
        Returns:
            bytes: Contenu PDF
        """
        try:
            # Générer le HTML programmatiquement
            html_content = PDFGenerationService.generate_receipt_html(receipt_data)
            
            # Générer le PDF avec WeasyPrint
            pdf_content = PDFGenerationService.generate_pdf_from_html(html_content)
            
            logger.info(f"Reçu PDF généré: {receipt_data.get('receipt_number', 'N/A')}")
            return pdf_content
            
        except Exception as e:
            logger.error(f"Erreur génération reçu PDF: {str(e)}")
            raise
    
    @staticmethod
    def generate_contract_pdf(contract_data):
        """
        Générer un contrat PDF avec cachet officiel.
        
        Args:
            contract_data: Données du contrat
            
        Returns:
            bytes: Contenu PDF
        """
        try:
            # Générer le HTML programmatiquement
            html_content = PDFGenerationService.generate_contract_html(contract_data)
            
            # Générer le PDF avec WeasyPrint
            pdf_content = PDFGenerationService.generate_pdf_from_html(html_content)
            
            logger.info(f"Contrat PDF généré: {contract_data.get('contract_number', 'N/A')}")
            return pdf_content
            
        except Exception as e:
            logger.error(f"Erreur génération contrat PDF: {str(e)}")
            raise
    
    @staticmethod
    def generate_invoice_html(invoice_data):
        """Générer le HTML pour une facture."""
        company_logo = PDFGenerationService.get_company_logo()
        company_stamp = PDFGenerationService.get_company_stamp()
        kleer_stamp = PDFGenerationService.get_kleer_infini_stamp()
        generation_date = timezone.now().strftime('%d/%m/%Y %H:%M')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Facture {invoice_data.get('invoice_number', '')}</title>
        </head>
        <body>
            <div class="header">
                {f'<img src="data:image/png;base64,{company_logo}" class="company-logo" alt="Logo Kleer Infini">' if company_logo else ''}
                <h1 class="document-title">FACTURE</h1>
                <p class="document-number">N° {invoice_data.get('invoice_number', '')}</p>
            </div>
            
            <div class="section">
                <h2 class="section-title">Informations Client</h2>
                <div class="info-grid">
                    <div class="info-row">
                        <div class="info-label">Nom du client:</div>
                        <div class="info-value">{invoice_data.get('client_name', '')}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Email:</div>
                        <div class="info-value">{invoice_data.get('client_email', '')}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Adresse:</div>
                        <div class="info-value">{invoice_data.get('client_address', '')}</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">Détails de l'Envoi</h2>
                <div class="info-grid">
                    <div class="info-row">
                        <div class="info-label">Numéro de suivi:</div>
                        <div class="info-value">{invoice_data.get('tracking_number', '')}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Origine:</div>
                        <div class="info-value">{invoice_data.get('origin', '')}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Destination:</div>
                        <div class="info-value">{invoice_data.get('destination', '')}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Poids:</div>
                        <div class="info-value">{invoice_data.get('weight', '')} kg</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">Détails de Facturation</h2>
                <table class="amount-table">
                    <thead>
                        <tr>
                            <th>Description</th>
                            <th>Montant (DA)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Frais de transport</td>
                            <td>{invoice_data.get('shipping_cost', 0):,.2f}</td>
                        </tr>
                        <tr>
                            <td>Frais d'emballage</td>
                            <td>{invoice_data.get('packaging_fee', 0):,.2f}</td>
                        </tr>
                        <tr>
                            <td>Commission Kleer Infini</td>
                            <td>{invoice_data.get('commission', 0):,.2f}</td>
                        </tr>
                        <tr class="total-row">
                            <td><strong>Total</strong></td>
                            <td><strong>{invoice_data.get('total_amount', 0):,.2f} DA</strong></td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="stamp-area">
                {f'<img src="data:image/png;base64,{company_stamp}" class="company-stamp" alt="Cachet entreprise">' if company_stamp else ''}
                {f'<img src="data:image/png;base64,{kleer_stamp}" class="kleer-infini-stamp" alt="Cachet Kleer Infini">' if kleer_stamp else ''}
            </div>
            
            <div class="footer">
                <p>Merci de votre confiance en Kleer Infini</p>
                <p class="generation-info">Document généré le {generation_date}</p>
            </div>
        </body>
        </html>
        """
        return html
    
    @staticmethod
    def generate_receipt_html(receipt_data):
        """Générer le HTML pour un reçu."""
        company_logo = PDFGenerationService.get_company_logo()
        digital_signature = PDFGenerationService.get_digital_signature()
        kleer_stamp = PDFGenerationService.get_kleer_infini_stamp()
        generation_date = timezone.now().strftime('%d/%m/%Y %H:%M')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Reçu {receipt_data.get('receipt_number', '')}</title>
        </head>
        <body>
            <div class="header">
                {f'<img src="data:image/png;base64,{company_logo}" class="company-logo" alt="Logo Kleer Infini">' if company_logo else ''}
                <h1 class="document-title">REÇU DE PAIEMENT</h1>
                <p class="document-number">N° {receipt_data.get('receipt_number', '')}</p>
            </div>
            
            <div class="section">
                <h2 class="section-title">Informations Client</h2>
                <div class="info-grid">
                    <div class="info-row">
                        <div class="info-label">Nom du client:</div>
                        <div class="info-value">{receipt_data.get('client_name', '')}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Email:</div>
                        <div class="info-value">{receipt_data.get('client_email', '')}</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">Détails du Paiement</h2>
                <div class="info-grid">
                    <div class="info-row">
                        <div class="info-label">Référence transaction:</div>
                        <div class="info-value">{receipt_data.get('transaction_reference', '')}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Méthode de paiement:</div>
                        <div class="info-value">{receipt_data.get('payment_method', '')}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Date de paiement:</div>
                        <div class="info-value">{receipt_data.get('payment_date', '')}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Montant payé:</div>
                        <div class="info-value"><strong>{receipt_data.get('amount_paid', 0):,.2f} DA</strong></div>
                    </div>
                </div>
            </div>
            
            <div class="signature-area">
                {f'<img src="data:image/png;base64,{digital_signature}" class="digital-signature" alt="Signature digitale">' if digital_signature else ''}
                {f'<img src="data:image/png;base64,{kleer_stamp}" class="kleer-infini-stamp" alt="Cachet Kleer Infini">' if kleer_stamp else ''}
            </div>
            
            <div class="footer">
                <p>Paiement confirmé et validé par Kleer Infini</p>
                <p class="generation-info">Document généré le {generation_date}</p>
            </div>
        </body>
        </html>
        """
        return html
    
    @staticmethod
    def generate_contract_html(contract_data):
        """Générer le HTML pour un contrat."""
        company_logo = PDFGenerationService.get_company_logo()
        official_stamp = PDFGenerationService.get_official_stamp()
        kleer_stamp = PDFGenerationService.get_kleer_infini_stamp()
        generation_date = timezone.now().strftime('%d/%m/%Y %H:%M')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Contrat {contract_data.get('contract_number', '')}</title>
        </head>
        <body>
            <div class="header">
                {f'<img src="data:image/png;base64,{company_logo}" class="company-logo" alt="Logo Kleer Infini">' if company_logo else ''}
                <h1 class="document-title">CONTRAT DE TRANSPORT</h1>
                <p class="document-number">N° {contract_data.get('contract_number', '')}</p>
            </div>
            
            <div class="section">
                <h2 class="section-title">Parties Contractantes</h2>
                <div class="info-grid">
                    <div class="info-row">
                        <div class="info-label">Expéditeur:</div>
                        <div class="info-value">{contract_data.get('sender_name', '')}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Voyageur:</div>
                        <div class="info-value">{contract_data.get('traveler_name', '')}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Destinataire:</div>
                        <div class="info-value">{contract_data.get('recipient_name', '')}</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">Détails du Transport</h2>
                <div class="info-grid">
                    <div class="info-row">
                        <div class="info-label">Date de départ:</div>
                        <div class="info-value">{contract_data.get('departure_date', '')}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Trajet:</div>
                        <div class="info-value">{contract_data.get('route', '')}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Poids du colis:</div>
                        <div class="info-value">{contract_data.get('package_weight', '')} kg</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Rémunération:</div>
                        <div class="info-value">{contract_data.get('compensation', 0):,.2f} DA</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">Conditions et Responsabilités</h2>
                <p>Le voyageur s'engage à :</p>
                <ul>
                    <li>Transporter le colis en toute sécurité</li>
                    <li>Respecter les délais convenus</li>
                    <li>Remettre le colis au destinataire désigné</li>
                    <li>Signaler tout incident immédiatement</li>
                </ul>
                
                <p>L'expéditeur s'engage à :</p>
                <ul>
                    <li>Fournir un colis conforme aux réglementations</li>
                    <li>Payer la rémunération convenue</li>
                    <li>Assurer la disponibilité du destinataire</li>
                </ul>
            </div>
            
            <div class="stamp-area">
                {f'<img src="data:image/png;base64,{official_stamp}" class="company-stamp" alt="Cachet officiel">' if official_stamp else ''}
                {f'<img src="data:image/png;base64,{kleer_stamp}" class="kleer-infini-stamp" alt="Cachet Kleer Infini">' if kleer_stamp else ''}
            </div>
            
            <div class="footer">
                <p>Contrat validé et sécurisé par Kleer Infini</p>
                <p class="generation-info">Document généré le {generation_date}</p>
            </div>
        </body>
        </html>
        """
        return html
    
    @staticmethod
    def generate_pdf_from_html(html_content, css_content=None):
        """
        Générer un PDF à partir de contenu HTML avec WeasyPrint.
        
        Args:
            html_content: Contenu HTML
            css_content: Contenu CSS (optionnel)
            
        Returns:
            bytes: Contenu PDF
        """
        try:
            # Configuration des polices
            font_config = FontConfiguration()
            
            # CSS par défaut si non fourni
            if not css_content:
                css_content = PDFGenerationService.get_default_css()
            
            # Créer l'objet HTML
            html = HTML(string=html_content)
            
            # Créer l'objet CSS
            css = CSS(string=css_content, font_config=font_config)
            
            # Générer le PDF
            pdf_bytes = html.write_pdf(stylesheets=[css], font_config=font_config)
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Erreur génération PDF WeasyPrint: {str(e)}")
            raise
    
    @staticmethod
    def get_company_logo():
        """Obtenir le logo de l'entreprise en base64."""
        try:
            logo_path = os.path.join(settings.STATIC_ROOT, 'images', 'kleer_infini_logo.png')
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as logo_file:
                    logo_data = logo_file.read()
                    return base64.b64encode(logo_data).decode('utf-8')
            return None
        except Exception as e:
            logger.warning(f"Impossible de charger le logo: {str(e)}")
            return None
    
    @staticmethod
    def get_company_stamp():
        """Obtenir le cachet de l'entreprise en base64."""
        try:
            stamp_path = os.path.join(settings.STATIC_ROOT, 'images', 'company_stamp.png')
            if os.path.exists(stamp_path):
                with open(stamp_path, 'rb') as stamp_file:
                    stamp_data = stamp_file.read()
                    return base64.b64encode(stamp_data).decode('utf-8')
            return None
        except Exception as e:
            logger.warning(f"Impossible de charger le cachet: {str(e)}")
            return None
    
    @staticmethod
    def get_kleer_infini_stamp():
        """Obtenir le cachet officiel Kleer Infini en base64."""
        try:
            stamp_path = os.path.join(settings.STATIC_ROOT, 'images', 'kleer_infini_stamp.png')
            if os.path.exists(stamp_path):
                with open(stamp_path, 'rb') as stamp_file:
                    stamp_data = stamp_file.read()
                    return base64.b64encode(stamp_data).decode('utf-8')
            return None
        except Exception as e:
            logger.warning(f"Impossible de charger le cachet Kleer Infini: {str(e)}")
            return None
    
    @staticmethod
    def get_official_stamp():
        """Obtenir le cachet officiel en base64."""
        try:
            stamp_path = os.path.join(settings.STATIC_ROOT, 'images', 'official_stamp.png')
            if os.path.exists(stamp_path):
                with open(stamp_path, 'rb') as stamp_file:
                    stamp_data = stamp_file.read()
                    return base64.b64encode(stamp_data).decode('utf-8')
            return None
        except Exception as e:
            logger.warning(f"Impossible de charger le cachet officiel: {str(e)}")
            return None
    
    @staticmethod
    def get_digital_signature():
        """Obtenir la signature digitale en base64."""
        try:
            signature_path = os.path.join(settings.STATIC_ROOT, 'images', 'digital_signature.png')
            if os.path.exists(signature_path):
                with open(signature_path, 'rb') as signature_file:
                    signature_data = signature_file.read()
                    return base64.b64encode(signature_data).decode('utf-8')
            return None
        except Exception as e:
            logger.warning(f"Impossible de charger la signature: {str(e)}")
            return None
    
    @staticmethod
    def get_default_css():
        """Obtenir le CSS par défaut pour les documents."""
        return """
        @page {
            size: A4;
            margin: 2cm;
            @top-center {
                content: "Kleer Infini - Plateforme d'Envoi Collaboratif";
                font-size: 10pt;
                color: #666;
            }
            @bottom-center {
                content: "Page " counter(page) " sur " counter(pages);
                font-size: 10pt;
                color: #666;
            }
        }
        
        body {
            font-family: 'Arial', sans-serif;
            font-size: 12pt;
            line-height: 1.4;
            color: #333;
        }
        
        .header {
            text-align: center;
            margin-bottom: 2cm;
            border-bottom: 2px solid #2c3e50;
            padding-bottom: 1cm;
        }
        
        .company-logo {
            max-width: 200px;
            max-height: 100px;
            margin-bottom: 1cm;
        }
        
        .document-title {
            font-size: 24pt;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 0.5cm;
        }
        
        .document-number {
            font-size: 14pt;
            color: #7f8c8d;
            margin-bottom: 1cm;
        }
        
        .section {
            margin-bottom: 1cm;
        }
        
        .section-title {
            font-size: 16pt;
            font-weight: bold;
            color: #2c3e50;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 0.3cm;
            margin-bottom: 0.5cm;
        }
        
        .info-grid {
            display: table;
            width: 100%;
            margin-bottom: 1cm;
        }
        
        .info-row {
            display: table-row;
        }
        
        .info-label {
            display: table-cell;
            font-weight: bold;
            width: 30%;
            padding: 0.2cm;
            background-color: #ecf0f1;
        }
        
        .info-value {
            display: table-cell;
            padding: 0.2cm;
            border-bottom: 1px solid #ecf0f1;
        }
        
        .amount-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1cm;
        }
        
        .amount-table th,
        .amount-table td {
            border: 1px solid #bdc3c7;
            padding: 0.3cm;
            text-align: left;
        }
        
        .amount-table th {
            background-color: #2c3e50;
            color: white;
            font-weight: bold;
        }
        
        .total-row {
            font-weight: bold;
            background-color: #ecf0f1;
        }
        
        .footer {
            margin-top: 2cm;
            text-align: center;
            border-top: 1px solid #bdc3c7;
            padding-top: 1cm;
        }
        
        .stamp-area {
            text-align: center;
            margin-top: 1cm;
        }
        
        .company-stamp {
            max-width: 150px;
            max-height: 150px;
            opacity: 0.8;
        }
        
        .kleer-infini-stamp {
            max-width: 120px;
            max-height: 120px;
            opacity: 0.9;
        }
        
        .signature-area {
            margin-top: 2cm;
            text-align: right;
        }
        
        .digital-signature {
            max-width: 200px;
            max-height: 100px;
        }
        
        .generation-info {
            font-size: 10pt;
            color: #7f8c8d;
            text-align: center;
            margin-top: 1cm;
        }
        """


class DocumentTemplateService:
    """Service pour la gestion des templates de documents."""
    
    @staticmethod
    def get_template_by_type(document_type):
        """
        Obtenir un template par type de document.
        
        Args:
            document_type: Type de document ('invoice', 'receipt', 'contract')
            
        Returns:
            DocumentTemplate: Template trouvé
        """
        try:
            from .models import DocumentTemplate
            return DocumentTemplate.objects.get(
                document_type=document_type,
                is_active=True
            )
        except DocumentTemplate.DoesNotExist:
            return None
    
    @staticmethod
    def create_default_templates():
        """Créer les templates par défaut."""
        try:
            from .models import DocumentTemplate
            
            # Template de facture
            invoice_template, created = DocumentTemplate.objects.get_or_create(
                document_type='invoice',
                defaults={
                    'name': 'Template Facture Standard',
                    'template_file': 'documents/templates/invoice_standard.html',
                    'is_active': True
                }
            )
            
            # Template de reçu
            receipt_template, created = DocumentTemplate.objects.get_or_create(
                document_type='receipt',
                defaults={
                    'name': 'Template Reçu Standard',
                    'template_file': 'documents/templates/receipt_standard.html',
                    'is_active': True
                }
            )
            
            # Template de contrat
            contract_template, created = DocumentTemplate.objects.get_or_create(
                document_type='contract',
                defaults={
                    'name': 'Template Contrat Standard',
                    'template_file': 'documents/templates/contract_standard.html',
                    'is_active': True
                }
            )
            
            logger.info("Templates par défaut créés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur création templates par défaut: {str(e)}")
            raise


class DocumentValidationService:
    """Service pour la validation des documents."""
    
    @staticmethod
    def validate_invoice_data(invoice_data):
        """
        Valider les données d'une facture.
        
        Args:
            invoice_data: Données de la facture
            
        Returns:
            dict: Résultat de la validation
        """
        required_fields = ['invoice_number', 'client_name', 'total_amount']
        missing_fields = []
        
        for field in required_fields:
            if field not in invoice_data or not invoice_data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            return {
                'valid': False,
                'errors': f"Champs manquants: {', '.join(missing_fields)}"
            }
        
        return {'valid': True}
    
    @staticmethod
    def validate_receipt_data(receipt_data):
        """
        Valider les données d'un reçu.
        
        Args:
            receipt_data: Données du reçu
            
        Returns:
            dict: Résultat de la validation
        """
        required_fields = ['receipt_number', 'client_name', 'amount_paid']
        missing_fields = []
        
        for field in required_fields:
            if field not in receipt_data or not receipt_data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            return {
                'valid': False,
                'errors': f"Champs manquants: {', '.join(missing_fields)}"
            }
        
        return {'valid': True}
