"""
Views for notifications app - Email and SMS notifications
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import random
import string
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Notification, EmailTemplate, SMSTemplate
from .serializers import (
    NotificationSerializer, EmailTemplateSerializer,
    SMSTemplateSerializer, EmailNotificationSerializer
)
from config.swagger_examples import (
    NOTIFICATION_EXAMPLE, ERROR_EXAMPLES
)
from config.swagger_config import (
    notification_send_schema, notification_list_schema
)


class EmailNotificationView(APIView):
    """Vue pour l'envoi d'emails."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Envoyer un email",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'template_name': openapi.Schema(type=openapi.TYPE_STRING),
                'recipient_email': openapi.Schema(type=openapi.TYPE_STRING),
                'context': openapi.Schema(type=openapi.TYPE_OBJECT)
            },
            required=['template_name', 'recipient_email']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Email envoyé",
                examples={"application/json": {
                    "success": True,
                    "message": "Email envoyé avec succès",
                    "notification_id": 1
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "message": "Nom du modèle et email du destinataire requis"
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Modèle non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Modèle d'email non trouvé"
                }}
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
                description="Erreur serveur",
                examples={"application/json": {
                    "success": False,
                    "message": "Erreur lors de l'envoi de l'email"
                }}
            )
        }
    )
    def post(self, request):
        """Envoyer un email."""
        template_name = request.data.get('template_name')
        recipient_email = request.data.get('recipient_email')
        context_data = request.data.get('context', {})
        
        if not template_name or not recipient_email:
            return Response({
                'success': False,
                'message': 'Nom du modèle et email du destinataire requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            template = EmailTemplate.objects.get(name=template_name, is_active=True)
            
            # Remplacer les variables dans le template
            subject = self.replace_variables(template.subject, context_data)
            body = self.replace_variables(template.body, context_data)
            
            # Envoyer l'email
            success = self.send_email(recipient_email, subject, body)
            
            if success:
                # Créer une notification
                notification = Notification.objects.create(
                    user=request.user,
                    notification_type='email',
                    title=f'Email envoyé à {recipient_email}',
                    message=f'Template: {template_name}',
                    status='sent'
                )
                
                return Response({
                    'success': True,
                    'message': 'Email envoyé avec succès',
                    'notification_id': notification.id
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Erreur lors de l\'envoi de l\'email'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except EmailTemplate.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Modèle d\'email non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def replace_variables(self, template_text, context):
        """Remplacer les variables dans le template."""
        for key, value in context.items():
            template_text = template_text.replace(f'{{{{{key}}}}}', str(value))
        return template_text
    
    def send_email(self, recipient_email, subject, body):
        """Envoyer un email."""
        try:
            # En production, configurer les paramètres SMTP
            # Pour la démonstration, on simule
            print(f"Email envoyé à {recipient_email}")
            print(f"Sujet: {subject}")
            print(f"Corps: {body}")
            
            # En production, utiliser send_mail
            # send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient_email])
            
            return True
        except Exception as e:
            print(f"Erreur d'envoi d'email: {e}")
            return False


class SMSNotificationView(APIView):
    """Vue pour l'envoi de SMS."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Envoyer un SMS",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'template_name': openapi.Schema(type=openapi.TYPE_STRING),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                'context': openapi.Schema(type=openapi.TYPE_OBJECT)
            },
            required=['template_name', 'phone_number']
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="SMS envoyé",
                examples={"application/json": {
                    "success": True,
                    "message": "SMS envoyé avec succès",
                    "notification_id": 2
                }}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "message": "Nom du modèle et numéro de téléphone requis"
                }}
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Modèle non trouvé",
                examples={"application/json": {
                    "success": False,
                    "message": "Modèle de SMS non trouvé"
                }}
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
                description="Erreur serveur",
                examples={"application/json": {
                    "success": False,
                    "message": "Erreur lors de l'envoi du SMS"
                }}
            )
        }
    )
    def post(self, request):
        """Envoyer un SMS."""
        template_name = request.data.get('template_name')
        phone_number = request.data.get('phone_number')
        context_data = request.data.get('context', {})
        
        if not template_name or not phone_number:
            return Response({
                'success': False,
                'message': 'Nom du modèle et numéro de téléphone requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            template = SMSTemplate.objects.get(name=template_name, is_active=True)
            
            # Remplacer les variables dans le template
            message = self.replace_variables(template.message, context_data)
            
            # Envoyer le SMS
            success = self.send_sms(phone_number, message)
            
            if success:
                # Créer une notification
                notification = Notification.objects.create(
                    user=request.user,
                    notification_type='sms',
                    title=f'SMS envoyé au {phone_number}',
                    message=f'Template: {template_name}',
                    status='sent'
                )
                
                return Response({
                    'success': True,
                    'message': 'SMS envoyé avec succès',
                    'notification_id': notification.id
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Erreur lors de l\'envoi du SMS'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except SMSTemplate.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Modèle de SMS non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def replace_variables(self, template_text, context):
        """Remplacer les variables dans le template."""
        for key, value in context.items():
            template_text = template_text.replace(f'{{{{{key}}}}}', str(value))
        return template_text
    
    def send_sms(self, phone_number, message):
        """Envoyer un SMS."""
        try:
            # En production, intégrer avec un service SMS
            # Pour la démonstration, on simule
            print(f"SMS envoyé au {phone_number}")
            print(f"Message: {message}")
            
            return True
        except Exception as e:
            print(f"Erreur d'envoi de SMS: {e}")
            return False


class NotificationListView(APIView):
    """Vue pour la liste des notifications."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Lister les notifications de l'utilisateur",
        manual_parameters=[
            openapi.Parameter(
                'notification_type',
                openapi.IN_QUERY,
                description="Type de notification",
                type=openapi.TYPE_STRING,
                enum=['email', 'sms', 'push', 'all']
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Statut de la notification",
                type=openapi.TYPE_STRING,
                enum=['sent', 'pending', 'failed', 'read', 'unread']
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Liste des notifications",
                examples={"application/json": {
                    "success": True,
                    "notifications": [
                        {
                            "id": 1,
                            "notification_type": "email",
                            "title": "Email envoyé à user@example.com",
                            "message": "Template: welcome_email",
                            "status": "sent",
                            "created_at": "2024-01-15T10:30:00Z"
                        }
                    ],
                    "count": 1
                }}
            )
        }
    )
    def get(self, request):
        """Récupérer la liste des notifications de l'utilisateur."""
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        serializer = NotificationSerializer(notifications, many=True)
        
        return Response({
            'success': True,
            'notifications': serializer.data,
            'count': notifications.count()
        })


class NotificationDetailView(APIView):
    """Vue pour les détails d'une notification."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        """Récupérer les détails d'une notification."""
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
            serializer = NotificationSerializer(notification)
            
            return Response({
                'success': True,
                'notification': serializer.data
            })
        except Notification.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Notification non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)


class MarkNotificationReadView(APIView):
    """Vue pour marquer une notification comme lue."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        """Marquer une notification comme lue."""
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
            
            return Response({
                'success': True,
                'message': 'Notification marquée comme lue'
            })
        except Notification.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Notification non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)


class MarkAllNotificationsReadView(APIView):
    """Vue pour marquer toutes les notifications comme lues."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Marquer toutes les notifications comme lues."""
        unread_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        )
        
        count = unread_notifications.count()
        unread_notifications.update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'success': True,
            'message': f'{count} notifications marquées comme lues'
        })


class EmailTemplateListView(APIView):
    """Vue pour la liste des modèles d'email."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupérer la liste des modèles d'email."""
        templates = EmailTemplate.objects.filter(is_active=True)
        serializer = EmailTemplateSerializer(templates, many=True)
        
        return Response({
            'success': True,
            'templates': serializer.data,
            'count': templates.count()
        })


class SMSTemplateListView(APIView):
    """Vue pour la liste des modèles de SMS."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupérer la liste des modèles de SMS."""
        templates = SMSTemplate.objects.filter(is_active=True)
        serializer = SMSTemplateSerializer(templates, many=True)
        
        return Response({
            'success': True,
            'templates': serializer.data,
            'count': templates.count()
        })


class NotificationAnalyticsView(APIView):
    """Vue pour les analytics des notifications."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupérer les statistiques des notifications."""
        user_notifications = Notification.objects.filter(user=request.user)
        
        analytics = {
            'total_notifications': user_notifications.count(),
            'email_notifications': user_notifications.filter(notification_type='email').count(),
            'sms_notifications': user_notifications.filter(notification_type='sms').count(),
            'unread_notifications': user_notifications.filter(is_read=False).count(),
            'sent_today': user_notifications.filter(
                created_at__date=timezone.now().date()
            ).count(),
            'sent_this_month': user_notifications.filter(
                created_at__month=timezone.now().month
            ).count()
        }
        
        return Response({
            'success': True,
            'analytics': analytics
        })


class SendShipmentNotificationView(APIView):
    """Vue pour envoyer des notifications d'envoi."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Envoyer une notification d'envoi."""
        shipment_id = request.data.get('shipment_id')
        notification_type = request.data.get('type', 'email')  # email ou sms
        
        if not shipment_id:
            return Response({
                'success': False,
                'message': 'ID d\'envoi requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from shipments.models import Shipment
            shipment = Shipment.objects.get(id=shipment_id, user=request.user)
            
            context = {
                'tracking_number': shipment.tracking_number,
                'origin': shipment.origin,
                'destination': shipment.destination,
                'status': shipment.get_status_display(),
                'customer_name': f"{shipment.user.first_name} {shipment.user.last_name}"
            }
            
            if notification_type == 'email':
                return self.send_shipment_email(shipment, context)
            elif notification_type == 'sms':
                return self.send_shipment_sms(shipment, context)
            else:
                return Response({
                    'success': False,
                    'message': 'Type de notification invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Shipment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Envoi non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def send_shipment_email(self, shipment, context):
        """Envoyer un email d'envoi."""
        try:
            template = EmailTemplate.objects.get(name='shipment_status', is_active=True)
            
            subject = self.replace_variables(template.subject, context)
            body = self.replace_variables(template.body, context)
            
            success = self.send_email(shipment.user.email, subject, body)
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Email d\'envoi envoyé avec succès'
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Erreur lors de l\'envoi de l\'email'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except EmailTemplate.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Modèle d\'email non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def send_shipment_sms(self, shipment, context):
        """Envoyer un SMS d'envoi."""
        try:
            template = SMSTemplate.objects.get(name='shipment_status', is_active=True)
            
            message = self.replace_variables(template.message, context)
            
            success = self.send_sms(shipment.user.userprofile.phone_number, message)
            
            if success:
                return Response({
                    'success': True,
                    'message': 'SMS d\'envoi envoyé avec succès'
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Erreur lors de l\'envoi du SMS'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except SMSTemplate.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Modèle de SMS non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def replace_variables(self, template_text, context):
        """Remplacer les variables dans le template."""
        for key, value in context.items():
            template_text = template_text.replace(f'{{{{{key}}}}}', str(value))
        return template_text
    
    def send_email(self, recipient_email, subject, body):
        """Envoyer un email."""
        try:
            print(f"Email envoyé à {recipient_email}")
            print(f"Sujet: {subject}")
            print(f"Corps: {body}")
            return True
        except Exception as e:
            print(f"Erreur d'envoi d'email: {e}")
            return False
    
    def send_sms(self, phone_number, message):
        """Envoyer un SMS."""
        try:
            print(f"SMS envoyé au {phone_number}")
            print(f"Message: {message}")
            return True
        except Exception as e:
            print(f"Erreur d'envoi de SMS: {e}")
            return False


# Views pour l'administration
class AdminNotificationListView(APIView):
    """Vue admin pour la liste de toutes les notifications."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Liste de toutes les notifications."""
        notifications = Notification.objects.all().select_related('user')
        serializer = NotificationSerializer(notifications, many=True)
        
        return Response({
            'success': True,
            'notifications': serializer.data,
            'count': notifications.count()
        })


class AdminEmailTemplateListView(APIView):
    """Vue admin pour la liste de tous les modèles d'email."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Liste de tous les modèles d'email."""
        templates = EmailTemplate.objects.all()
        serializer = EmailTemplateSerializer(templates, many=True)
        
        return Response({
            'success': True,
            'templates': serializer.data,
            'count': templates.count()
        })


class AdminSMSTemplateListView(APIView):
    """Vue admin pour la liste de tous les modèles de SMS."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Liste de tous les modèles de SMS."""
        templates = SMSTemplate.objects.all()
        serializer = SMSTemplateSerializer(templates, many=True)
        
        return Response({
            'success': True,
            'templates': serializer.data,
            'count': templates.count()
        })
