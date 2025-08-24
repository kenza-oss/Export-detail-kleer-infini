"""
Tests for admin_panel app - Dashboard and Analytics for Administrators
"""

import os
import tempfile
import shutil
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import timedelta
import json

from .models import (
    DashboardMetric, AdminReport, AdminNotification, 
    SystemHealth, AdminAuditLog
)
from users.models import User
from shipments.models import Shipment
from payments.models import Transaction, Wallet
from trips.models import Trip

User = get_user_model()

# Configuration pour désactiver certaines fonctionnalités pendant les tests
@override_settings(DJANGO_TESTING='true')
class BaseAdminPanelTestCase(TestCase):
    """Classe de base pour tous les tests du module admin_panel."""
    
    def setUp(self):
        """Configuration initiale commune."""
        super().setUp()
        # Désactiver certaines fonctionnalités pour les tests
        os.environ['DJANGO_TESTING'] = 'true'
    
    def tearDown(self):
        """Nettoyage commun."""
        super().tearDown()
        # Réactiver les fonctionnalités
        if 'DJANGO_TESTING' in os.environ:
            del os.environ['DJANGO_TESTING']


class DashboardMetricModelTests(BaseAdminPanelTestCase):
    """Tests unitaires pour le modèle DashboardMetric."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        super().setUp()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_metric_creation(self):
        """Test de création d'une métrique du tableau de bord."""
        metric = DashboardMetric.objects.create(
            metric_type='shipments',
            period_type='daily',
            period_start=timezone.now(),
            period_end=timezone.now() + timedelta(days=1),
            value=150.00,
            previous_value=120.00,
            change_percentage=25.00,
            metadata={'source': 'test'}
        )
        
        self.assertEqual(metric.metric_type, 'shipments')
        self.assertEqual(metric.period_type, 'daily')
        self.assertEqual(metric.value, 150.00)
        self.assertEqual(metric.change_percentage, 25.00)
        self.assertIsNotNone(metric.id)
    
    def test_metric_trend_direction(self):
        """Test de la direction de tendance des métriques."""
        # Métrique en hausse
        up_metric = DashboardMetric.objects.create(
            metric_type='payments',
            period_type='weekly',
            period_start=timezone.now(),
            period_end=timezone.now() + timedelta(weeks=1),
            value=1000.00,
            previous_value=800.00,
            change_percentage=25.00
        )
        self.assertEqual(up_metric.trend_direction, 'up')
        
        # Métrique en baisse
        down_metric = DashboardMetric.objects.create(
            metric_type='users',
            period_type='monthly',
            period_start=timezone.now(),
            period_end=timezone.now() + timedelta(days=30),
            value=50.00,
            previous_value=60.00,
            change_percentage=-16.67
        )
        self.assertEqual(down_metric.trend_direction, 'down')
        
        # Métrique neutre
        neutral_metric = DashboardMetric.objects.create(
            metric_type='commissions',
            period_type='daily',
            period_start=timezone.now(),
            period_end=timezone.now() + timedelta(days=1),
            value=100.00,
            previous_value=None,
            change_percentage=None
        )
        self.assertEqual(neutral_metric.trend_direction, 'neutral')
    
    def test_metric_string_representation(self):
        """Test de la représentation string du modèle."""
        metric = DashboardMetric.objects.create(
            metric_type='shipments',
            period_type='daily',
            period_start=timezone.now(),
            period_end=timezone.now() + timedelta(days=1),
            value=150.00
        )
        
        expected_string = f"Envois - Quotidien ({metric.period_start.strftime('%Y-%m-%d')})"
        self.assertEqual(str(metric), expected_string)


class AdminReportModelTests(BaseAdminPanelTestCase):
    """Tests unitaires pour le modèle AdminReport."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        super().setUp()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_report_creation(self):
        """Test de création d'un rapport administratif."""
        report = AdminReport.objects.create(
            name='Test Report',
            report_type='shipments_summary',
            format='json',
            parameters={'date_from': '2024-01-01'},
            filters={'status': 'delivered'},
            generated_by=self.user
        )
        
        self.assertEqual(report.name, 'Test Report')
        self.assertEqual(report.report_type, 'shipments_summary')
        self.assertEqual(report.format, 'json')
        self.assertEqual(report.parameters, {'date_from': '2024-01-01'})
        self.assertEqual(report.filters, {'status': 'delivered'})
        self.assertEqual(report.generated_by, self.user)
    
    def test_report_string_representation(self):
        """Test de la représentation string du modèle."""
        report = AdminReport.objects.create(
            name='Test Report',
            report_type='shipments_summary',
            format='json'
        )
        
        expected_string = f"Test Report (Résumé des envois) - {report.generated_at.strftime('%Y-%m-%d')}"
        self.assertEqual(str(report), expected_string)


class AdminNotificationModelTests(BaseAdminPanelTestCase):
    """Tests unitaires pour le modèle AdminNotification."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        super().setUp()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_notification_creation(self):
        """Test de création d'une notification administrative."""
        notification = AdminNotification.objects.create(
            title='Test Notification',
            message='This is a test notification',
            notification_type='info',
            priority='normal',
            is_broadcast=True
        )
        notification.recipients.add(self.user)
        
        self.assertEqual(notification.title, 'Test Notification')
        self.assertEqual(notification.message, 'This is a test notification')
        self.assertEqual(notification.notification_type, 'info')
        self.assertEqual(notification.priority, 'normal')
        self.assertTrue(notification.is_broadcast)
        self.assertEqual(notification.recipients.count(), 1)
    
    def test_notification_expiration(self):
        """Test de l'expiration des notifications."""
        # Notification non expirée
        active_notification = AdminNotification.objects.create(
            title='Active Notification',
            message='This notification is active',
            expires_at=timezone.now() + timedelta(days=1)
        )
        self.assertFalse(active_notification.is_expired)
        
        # Notification expirée
        expired_notification = AdminNotification.objects.create(
            title='Expired Notification',
            message='This notification is expired',
            expires_at=timezone.now() - timedelta(days=1)
        )
        self.assertTrue(expired_notification.is_expired)
        
        # Notification sans expiration
        no_expiry_notification = AdminNotification.objects.create(
            title='No Expiry Notification',
            message='This notification has no expiry'
        )
        self.assertFalse(no_expiry_notification.is_expired)
    
    def test_notification_string_representation(self):
        """Test de la représentation string du modèle."""
        notification = AdminNotification.objects.create(
            title='Test Notification',
            message='Test message',
            priority='high'
        )
        
        expected_string = f"Test Notification (Élevée) - {notification.created_at.strftime('%Y-%m-%d %H:%M')}"
        self.assertEqual(str(notification), expected_string)


class SystemHealthModelTests(BaseAdminPanelTestCase):
    """Tests unitaires pour le modèle SystemHealth."""
    
    def test_system_health_creation(self):
        """Test de création d'un statut de santé système."""
        health = SystemHealth.objects.create(
            service_name='database',
            status='healthy',
            response_time=timedelta(milliseconds=50),
            uptime_percentage=99.95,
            error_count=0,
            details={'connection_pool': 'active'}
        )
        
        self.assertEqual(health.service_name, 'database')
        self.assertEqual(health.status, 'healthy')
        self.assertEqual(health.response_time, timedelta(milliseconds=50))
        self.assertEqual(health.uptime_percentage, 99.95)
        self.assertEqual(health.error_count, 0)
        self.assertEqual(health.details, {'connection_pool': 'active'})
    
    def test_system_health_string_representation(self):
        """Test de la représentation string du modèle."""
        health = SystemHealth.objects.create(
            service_name='api',
            status='warning'
        )
        
        expected_string = "api - Avertissement"
        self.assertEqual(str(health), expected_string)


class AdminAuditLogModelTests(BaseAdminPanelTestCase):
    """Tests unitaires pour le modèle AdminAuditLog."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        super().setUp()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_audit_log_creation(self):
        """Test de création d'un log d'audit."""
        audit_log = AdminAuditLog.objects.create(
            user=self.user,
            action='create',
            model_name='shipment',
            object_id='123',
            changes={'status': 'pending'},
            ip_address='127.0.0.1',
            user_agent='Test User Agent'
        )
        
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.action, 'create')
        self.assertEqual(audit_log.model_name, 'shipment')
        self.assertEqual(audit_log.object_id, '123')
        self.assertEqual(audit_log.changes, {'status': 'pending'})
        self.assertEqual(audit_log.ip_address, '127.0.0.1')
    
    def test_audit_log_string_representation(self):
        """Test de la représentation string du modèle."""
        audit_log = AdminAuditLog.objects.create(
            user=self.user,
            action='update',
            model_name='user'
        )
        
        expected_string = f"{self.user.username} - Modification - {audit_log.timestamp.strftime('%Y-%m-%d %H:%M')}"
        self.assertEqual(str(audit_log), expected_string)


class DashboardOverviewAPITests(APITestCase):
    """Tests d'API pour la vue d'ensemble du tableau de bord."""
    
    def setUp(self):
        """Configuration initiale pour les tests d'API."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_superuser=True
        )
        
        self.regular_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        self.client.force_authenticate(user=self.admin_user)
    
    def test_dashboard_overview_endpoint(self):
        """Test de l'endpoint de vue d'ensemble du tableau de bord."""
        response = self.client.get('/api/v1/admin/dashboard/overview/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('timestamp', response.data)
    
    def test_dashboard_overview_unauthorized(self):
        """Test d'accès sans privilèges admin."""
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.get('/api/v1/admin/dashboard/overview/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_dashboard_overview_unauthenticated(self):
        """Test d'accès sans authentification."""
        self.client.force_authenticate(user=None)
        
        response = self.client.get('/api/v1/admin/dashboard/overview/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DashboardMetricsAPITests(APITestCase):
    """Tests d'API pour la gestion des métriques du tableau de bord."""
    
    def setUp(self):
        """Configuration initiale pour les tests d'API."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_superuser=True
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Créer des métriques de test
        self.metric = DashboardMetric.objects.create(
            metric_type='shipments',
            period_type='daily',
            period_start=timezone.now(),
            period_end=timezone.now() + timedelta(days=1),
            value=150.00,
            is_active=True
        )
    
    def test_metrics_list_endpoint(self):
        """Test de l'endpoint de liste des métriques."""
        response = self.client.get('/api/v1/admin/dashboard/metrics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
    
    def test_metrics_filtered_by_type(self):
        """Test de filtrage des métriques par type."""
        response = self.client.get('/api/v1/admin/dashboard/metrics/?type=shipments')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
    
    def test_metrics_filtered_by_period(self):
        """Test de filtrage des métriques par période."""
        response = self.client.get('/api/v1/admin/dashboard/metrics/?period=daily')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
    
    def test_create_metric_endpoint(self):
        """Test de création d'une nouvelle métrique."""
        data = {
            'metric_type': 'payments',
            'period_type': 'weekly',
            'period_start': timezone.now().isoformat(),
            'period_end': (timezone.now() + timedelta(weeks=1)).isoformat(),
            'value': '1000.00',
            'metadata': {'source': 'test'}
        }
        
        response = self.client.post('/api/v1/admin/dashboard/metrics/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('data', response.data)


class ReportsAPITests(APITestCase):
    """Tests d'API pour la gestion des rapports."""
    
    def setUp(self):
        """Configuration initiale pour les tests d'API."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_superuser=True
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Créer un rapport de test
        self.report = AdminReport.objects.create(
            name='Test Report',
            report_type='shipments_summary',
            format='json',
            generated_by=self.admin_user
        )
    
    def test_reports_list_endpoint(self):
        """Test de l'endpoint de liste des rapports."""
        response = self.client.get('/api/v1/admin/reports/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
    
    def test_report_detail_endpoint(self):
        """Test de l'endpoint de détail d'un rapport."""
        response = self.client.get(f'/api/v1/admin/reports/{self.report.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
    
    def test_create_report_endpoint(self):
        """Test de création d'un nouveau rapport."""
        data = {
            'report_type': 'financial_summary',
            'format': 'excel',
            'date_from': '2024-01-01',
            'date_to': '2024-01-31',
            'filters': {},
            'include_charts': True,
            'include_metadata': True
        }
        
        response = self.client.post('/api/v1/admin/reports/', data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('data', response.data)


class NotificationsAPITests(APITestCase):
    """Tests d'API pour la gestion des notifications."""
    
    def setUp(self):
        """Configuration initiale pour les tests d'API."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_superuser=True
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Créer une notification de test
        self.notification = AdminNotification.objects.create(
            title='Test Notification',
            message='This is a test notification',
            notification_type='info',
            priority='normal'
        )
    
    def test_notifications_list_endpoint(self):
        """Test de l'endpoint de liste des notifications."""
        response = self.client.get('/api/v1/admin/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
    
    def test_notification_detail_endpoint(self):
        """Test de l'endpoint de détail d'une notification."""
        response = self.client.get(f'/api/v1/admin/notifications/{self.notification.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
    
    def test_create_notification_endpoint(self):
        """Test de création d'une nouvelle notification."""
        data = {
            'title': 'Test Alert',
            'message': 'This is a test alert',
            'notification_type': 'warning',
            'priority': 'high',
            'is_broadcast': True,
            'recipients': [self.admin_user.id]
        }
        
        response = self.client.post('/api/v1/admin/notifications/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('data', response.data)
    
    def test_mark_notification_read_endpoint(self):
        """Test de marquage d'une notification comme lue."""
        response = self.client.post(f'/api/v1/admin/notifications/{self.notification.id}/mark-read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que la notification est marquée comme lue
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)


class SystemHealthAPITests(APITestCase):
    """Tests d'API pour la surveillance de la santé du système."""
    
    def setUp(self):
        """Configuration initiale pour les tests d'API."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_superuser=True
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Créer un statut de santé de test
        self.health = SystemHealth.objects.create(
            service_name='database',
            status='healthy',
            response_time=timedelta(milliseconds=50),
            uptime_percentage=99.95
        )
    
    def test_system_health_endpoint(self):
        """Test de l'endpoint de santé du système."""
        response = self.client.get('/api/v1/admin/system/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
    
    def test_system_health_specific_service(self):
        """Test de santé d'un service spécifique."""
        response = self.client.get('/api/v1/admin/system/health/?service_name=database')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
    
    def test_update_system_health_endpoint(self):
        """Test de mise à jour du statut de santé."""
        data = {
            'service_name': 'api',
            'status': 'warning',
            'response_time': '00:00:00.100000',
            'uptime_percentage': 98.50,
            'error_count': 5,
            'details': {'last_error': 'Connection timeout'}
        }
        
        response = self.client.put('/api/v1/admin/system/health/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)


class AuditLogsAPITests(APITestCase):
    """Tests d'API pour la consultation des logs d'audit."""
    
    def setUp(self):
        """Configuration initiale pour les tests d'API."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_superuser=True
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        # Créer un log d'audit de test
        self.audit_log = AdminAuditLog.objects.create(
            user=self.admin_user,
            action='create',
            model_name='shipment',
            object_id='123',
            changes={'status': 'pending'},
            ip_address='127.0.0.1'
        )
    
    def test_audit_logs_endpoint(self):
        """Test de l'endpoint de liste des logs d'audit."""
        response = self.client.get('/api/v1/admin/audit/logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
    
    def test_audit_logs_filtered_by_user(self):
        """Test de filtrage des logs par utilisateur."""
        response = self.client.get(f'/api/v1/admin/audit/logs/?user={self.admin_user.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
    
    def test_audit_logs_filtered_by_action(self):
        """Test de filtrage des logs par action."""
        response = self.client.get('/api/v1/admin/audit/logs/?action=create')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
    
    def test_audit_logs_filtered_by_model(self):
        """Test de filtrage des logs par modèle."""
        response = self.client.get('/api/v1/admin/audit/logs/?model_name=shipment')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
    
    def test_audit_log_detail_endpoint(self):
        """Test de l'endpoint de détail d'un log d'audit."""
        response = self.client.get(f'/api/v1/admin/audit/logs/{self.audit_log.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)


class QuickActionsAPITests(APITestCase):
    """Tests d'API pour les actions rapides."""
    
    def setUp(self):
        """Configuration initiale pour les tests d'API."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_superuser=True
        )
        
        self.client.force_authenticate(user=self.admin_user)
    
    def test_quick_actions_endpoint(self):
        """Test de l'endpoint des actions rapides."""
        response = self.client.get('/api/v1/admin/quick-actions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
    
    def test_execute_quick_action_endpoint(self):
        """Test d'exécution d'une action rapide."""
        data = {
            'action': 'cleanup_expired_otps',
            'parameters': {
                'confirm': True
            }
        }
        
        response = self.client.post('/api/v1/admin/quick-actions/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])


class ExportDataAPITests(APITestCase):
    """Tests d'API pour l'export de données."""
    
    def setUp(self):
        """Configuration initiale pour les tests d'API."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_superuser=True
        )
        
        self.client.force_authenticate(user=self.admin_user)
    
    def test_export_data_endpoint(self):
        """Test de l'endpoint d'export de données."""
        data = {
            'report_type': 'shipments',
            'format': 'excel',
            'date_from': '2024-01-01',
            'date_to': '2024-01-31',
            'filters': {
                'status': ['delivered', 'in_transit']
            }
        }
        
        response = self.client.post('/api/v1/admin/export/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])
    
    def test_export_users_data(self):
        """Test d'export des données utilisateurs."""
        data = {
            'report_type': 'users',
            'format': 'csv',
            'filters': {
                'role': 'all',
                'verification_status': 'all'
            }
        }
        
        response = self.client.post('/api/v1/admin/export/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])
    
    def test_export_payments_data(self):
        """Test d'export des données de paiements."""
        data = {
            'report_type': 'payments',
            'format': 'pdf',
            'date_from': '2024-01-01',
            'date_to': '2024-01-31',
            'filters': {
                'payment_method': 'all',
                'status': 'completed'
            }
        }
        
        response = self.client.post('/api/v1/admin/export/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])
