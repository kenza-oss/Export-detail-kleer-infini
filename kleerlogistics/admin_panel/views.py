"""
Views for admin_panel app - Dashboard and Analytics for Administrators
"""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db import transaction
from django.utils import timezone

from .serializers import (
    DashboardOverviewSerializer, ExportReportSerializer, ExportDataSerializer, SystemHealthCheckSerializer,
    DashboardMetricSerializer, AdminReportSerializer, AdminNotificationSerializer,
    SystemHealthSerializer, AdminAuditLogSerializer
)
from .services import (
    DashboardService, ReportService, NotificationService, 
    SystemHealthService, AuditService
)
from .models import (
    DashboardMetric, AdminReport, AdminNotification, 
    SystemHealth, AdminAuditLog
)

logger = logging.getLogger(__name__)


class DashboardOverviewView(APIView):
    """Vue pour la vue d'ensemble du tableau de bord administratif."""
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    @method_decorator(cache_page(60 * 5))  # Cache de 5 minutes
    def get(self, request):
        """Récupère la vue d'ensemble complète du tableau de bord."""
        try:
            # Enregistrer l'action dans les logs d'audit
            AuditService.log_action(
                user=request.user,
                action='view',
                model_name='dashboard',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                session_id=request.session.session_key,
            )
            
            # Récupérer les données du tableau de bord
            dashboard_data = DashboardService.get_dashboard_overview()
            
            # Sérialiser les données
            serializer = DashboardOverviewSerializer(data=dashboard_data)
            if serializer.is_valid():
                return Response({
                    'success': True,
                    'data': serializer.data,
                    'timestamp': timezone.now().isoformat(),
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Erreur de sérialisation des données',
                    'errors': serializer.errors
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error in dashboard overview: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la récupération du tableau de bord'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DashboardMetricsView(APIView):
    """Vue pour la gestion des métriques du tableau de bord."""
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        """Récupère les métriques du tableau de bord."""
        try:
            metric_type = request.query_params.get('type')
            period_type = request.query_params.get('period')
            
            filters = {}
            if metric_type:
                filters['metric_type'] = metric_type
            if period_type:
                filters['period_type'] = period_type
            
            metrics = DashboardMetric.objects.filter(**filters, is_active=True)
            serializer = DashboardMetricSerializer(metrics, many=True)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'count': metrics.count()
            })
            
        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la récupération des métriques'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Crée une nouvelle métrique du tableau de bord."""
        try:
            serializer = DashboardMetricSerializer(data=request.data)
            if serializer.is_valid():
                metric = serializer.save()
                
                # Enregistrer l'action dans les logs d'audit
                AuditService.log_action(
                    user=request.user,
                    action='create',
                    model_name='DashboardMetric',
                    object_id=str(metric.id),
                    changes=request.data,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    session_id=request.session.session_key,
                )
                
                return Response({
                    'success': True,
                    'message': 'Métrique créée avec succès',
                    'data': DashboardMetricSerializer(metric).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': 'Données invalides',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error creating dashboard metric: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la création de la métrique'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportsView(APIView):
    """Vue pour la gestion des rapports administratifs."""
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        """Récupère la liste des rapports."""
        try:
            report_type = request.query_params.get('type')
            format_type = request.query_params.get('format')
            
            filters = {}
            if report_type:
                filters['report_type'] = report_type
            if format_type:
                filters['format'] = format_type
            
            reports = AdminReport.objects.filter(**filters)
            serializer = AdminReportSerializer(reports, many=True)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'count': reports.count()
            })
            
        except Exception as e:
            logger.error(f"Error getting reports: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la récupération des rapports'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Génère un nouveau rapport."""
        try:
            serializer = ExportReportSerializer(data=request.data)
            if serializer.is_valid():
                data = serializer.validated_data
                
                # Générer le rapport
                report = ReportService.generate_report(
                    report_type=data['report_type'],
                    format=data['format'],
                    filters=data.get('filters'),
                    parameters={
                        'user': request.user,
                        'include_charts': data.get('include_charts', False),
                        'include_metadata': data.get('include_metadata', True),
                    }
                )
                
                if report:
                    # Enregistrer l'action dans les logs d'audit
                    AuditService.log_action(
                        user=request.user,
                        action='create',
                        model_name='AdminReport',
                        object_id=str(report.id),
                        changes=data,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT'),
                        session_id=request.session.session_key,
                    )
                    
                    return Response({
                        'success': True,
                        'message': 'Rapport généré avec succès',
                        'data': AdminReportSerializer(report).data
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'success': False,
                        'message': 'Erreur lors de la génération du rapport'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({
                    'success': False,
                    'message': 'Données invalides',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la génération du rapport'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportDetailView(APIView):
    """Vue pour la gestion d'un rapport spécifique."""
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request, report_id):
        """Récupère les détails d'un rapport."""
        try:
            try:
                report = AdminReport.objects.get(id=report_id)
            except AdminReport.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Rapport non trouvé'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = AdminReportSerializer(report)
            
            # Enregistrer l'action dans les logs d'audit
            AuditService.log_action(
                user=request.user,
                action='view',
                model_name='AdminReport',
                object_id=str(report.id),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                session_id=request.session.session_key,
            )
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error getting report details: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la récupération du rapport'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, report_id):
        """Supprime un rapport."""
        try:
            try:
                report = AdminReport.objects.get(id=report_id)
            except AdminReport.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Rapport non trouvé'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Enregistrer l'action dans les logs d'audit
            AuditService.log_action(
                user=request.user,
                action='delete',
                model_name='AdminReport',
                object_id=str(report.id),
                changes={'deleted': True},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                session_id=request.session.session_key,
            )
            
            report.delete()
            
            return Response({
                'success': True,
                'message': 'Rapport supprimé avec succès'
            })
            
        except Exception as e:
            logger.error(f"Error deleting report: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la suppression du rapport'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationsView(APIView):
    """Vue pour la gestion des notifications administratives."""
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        """Récupère la liste des notifications."""
        try:
            notification_type = request.query_params.get('type')
            priority = request.query_params.get('priority')
            is_read = request.query_params.get('is_read')
            
            filters = {}
            if notification_type:
                filters['notification_type'] = notification_type
            if priority:
                filters['priority'] = priority
            if is_read is not None:
                filters['is_read'] = is_read.lower() == 'true'
            
            notifications = AdminNotification.objects.filter(**filters)
            serializer = AdminNotificationSerializer(notifications, many=True)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'count': notifications.count()
            })
            
        except Exception as e:
            logger.error(f"Error getting notifications: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la récupération des notifications'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Crée une nouvelle notification."""
        try:
            serializer = AdminNotificationSerializer(data=request.data)
            if serializer.is_valid():
                notification = serializer.save()
                
                # Enregistrer l'action dans les logs d'audit
                AuditService.log_action(
                    user=request.user,
                    action='create',
                    model_name='AdminNotification',
                    object_id=str(notification.id),
                    changes=request.data,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    session_id=request.session.session_key,
                )
                
                return Response({
                    'success': True,
                    'message': 'Notification créée avec succès',
                    'data': AdminNotificationSerializer(notification).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': 'Données invalides',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la création de la notification'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationDetailView(APIView):
    """Vue pour la gestion d'une notification spécifique."""
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request, notification_id):
        """Récupère les détails d'une notification."""
        try:
            try:
                notification = AdminNotification.objects.get(id=notification_id)
            except AdminNotification.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Notification non trouvée'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = AdminNotificationSerializer(notification)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error getting notification details: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la récupération de la notification'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, notification_id):
        """Marque une notification comme lue."""
        try:
            success = NotificationService.mark_as_read(notification_id, request.user)
            
            if success:
                # Enregistrer l'action dans les logs d'audit
                AuditService.log_action(
                    user=request.user,
                    action='update',
                    model_name='AdminNotification',
                    object_id=notification_id,
                    changes={'marked_as_read': True},
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    session_id=request.session.session_key,
                )
                
                return Response({
                    'success': True,
                    'message': 'Notification marquée comme lue'
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Erreur lors du marquage de la notification'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors du marquage de la notification'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SystemHealthView(APIView):
    """Vue pour la surveillance de la santé du système."""
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        """Récupère l'état de santé du système."""
        try:
            services = SystemHealth.objects.all()
            serializer = SystemHealthSerializer(services, many=True)
            
            # Enregistrer l'action dans les logs d'audit
            AuditService.log_action(
                user=request.user,
                action='view',
                model_name='SystemHealth',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                session_id=request.session.session_key,
            )
            
            return Response({
                'success': True,
                'data': serializer.data,
                'overall_status': 'healthy' if not services.filter(status='critical').exists() else 'critical'
            })
            
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la récupération de la santé du système'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Lance une vérification de santé du système."""
        try:
            serializer = SystemHealthCheckSerializer(data=request.data)
            if serializer.is_valid():
                data = serializer.validated_data
                
                # Effectuer la vérification de santé
                health_checks = SystemHealthService.check_system_health()
                
                # Enregistrer l'action dans les logs d'audit
                AuditService.log_action(
                    user=request.user,
                    action='view',
                    model_name='SystemHealth',
                    changes={'health_check_requested': True, 'parameters': data},
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    session_id=request.session.session_key,
                )
                
                return Response({
                    'success': True,
                    'message': 'Vérification de santé effectuée',
                    'data': health_checks
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Données invalides',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error checking system health: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la vérification de santé'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request):
        """Met à jour le statut de santé d'un service."""
        try:
            serializer = SystemHealthSerializer(data=request.data)
            if serializer.is_valid():
                data = serializer.validated_data
                
                # Mettre à jour ou créer le statut de santé
                service_name = data.get('service_name')
                if service_name:
                    health, created = SystemHealth.objects.update_or_create(
                        service_name=service_name,
                        defaults=data
                    )
                    
                    # Enregistrer l'action dans les logs d'audit
                    AuditService.log_action(
                        user=request.user,
                        action='update' if not created else 'create',
                        model_name='SystemHealth',
                        object_id=service_name,
                        changes=data,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT'),
                        session_id=request.session.session_key,
                    )
                    
                    return Response({
                        'success': True,
                        'message': 'Statut de santé mis à jour',
                        'data': SystemHealthSerializer(health).data
                    })
                else:
                    return Response({
                        'success': False,
                        'message': 'Nom du service requis'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'success': False,
                    'message': 'Données invalides',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error updating system health: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la mise à jour du statut de santé'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AuditLogsView(APIView):
    """Vue pour la consultation des logs d'audit."""
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request, log_id=None):
        """Récupère les logs d'audit."""
        try:
            # Si un ID est fourni, retourner le détail du log
            if log_id:
                try:
                    log = AdminAuditLog.objects.get(id=log_id)
                    serializer = AdminAuditLogSerializer(log)
                    return Response({
                        'success': True,
                        'data': serializer.data
                    })
                except AdminAuditLog.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'Log d\'audit non trouvé'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # Sinon, retourner la liste des logs
            action_type = request.query_params.get('action')
            model_name = request.query_params.get('model')
            user_id = request.query_params.get('user')
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            
            filters = {}
            if action_type:
                filters['action'] = action_type
            if model_name:
                filters['model_name'] = model_name
            if user_id:
                filters['user_id'] = user_id
            
            logs = AdminAuditLog.objects.filter(**filters)
            
            # Filtrage par date
            if date_from:
                logs = logs.filter(timestamp__date__gte=date_from)
            if date_to:
                logs = logs.filter(timestamp__date__lte=date_to)
            
            # Pagination
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 50))
            start = (page - 1) * page_size
            end = start + page_size
            
            logs_page = logs[start:end]
            serializer = AdminAuditLogSerializer(logs_page, many=True)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': logs.count(),
                    'total_pages': (logs.count() + page_size - 1) // page_size
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting audit logs: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la récupération des logs d\'audit'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QuickActionsView(APIView):
    """Vue pour les actions rapides du tableau de bord."""
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        """Récupère les actions rapides disponibles."""
        try:
            quick_actions = DashboardService.get_quick_actions()
            
            # Filtrer selon les permissions de l'utilisateur
            filtered_actions = []
            for action in quick_actions:
                if request.user.has_perm(action.get('permission', '')):
                    filtered_actions.append(action)
            
            return Response({
                'success': True,
                'data': filtered_actions,
                'count': len(filtered_actions)
            })
            
        except Exception as e:
            logger.error(f"Error getting quick actions: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de la récupération des actions rapides'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Exécute une action rapide."""
        try:
            action_name = request.data.get('action')
            parameters = request.data.get('parameters', {})
            
            if not action_name:
                return Response({
                    'success': False,
                    'message': 'Nom de l\'action requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Enregistrer l'action dans les logs d'audit
            AuditService.log_action(
                user=request.user,
                action='execute',
                model_name='QuickAction',
                object_id=action_name,
                changes=parameters,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                session_id=request.session.session_key,
            )
            
            # Ici, vous pouvez implémenter la logique d'exécution des actions
            # selon l'action demandée
            
            return Response({
                'success': True,
                'message': f'Action {action_name} exécutée avec succès',
                'action': action_name,
                'parameters': parameters
            })
            
        except Exception as e:
            logger.error(f"Error executing quick action: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de l\'exécution de l\'action'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExportDataView(APIView):
    """Vue pour l'export de données."""
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request):
        """Exporte les données selon les paramètres spécifiés."""
        try:
            serializer = ExportDataSerializer(data=request.data)
            if serializer.is_valid():
                data = serializer.validated_data
                
                # Enregistrer l'action dans les logs d'audit
                AuditService.log_action(
                    user=request.user,
                    action='export',
                    model_name='data_export',
                    changes=data,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    session_id=request.session.session_key,
                )
                
                # Ici, vous pouvez implémenter la logique d'export
                # selon le format demandé (CSV, PDF, Excel, etc.)
                
                return Response({
                    'success': True,
                    'message': 'Export en cours de préparation',
                    'export_id': 'export_' + str(int(timezone.now().timestamp())),
                    'format': data['format'],
                    'estimated_time': '2-5 minutes'
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Données invalides',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            return Response({
                'success': False,
                'message': 'Erreur lors de l\'export des données'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
