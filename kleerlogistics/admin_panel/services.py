"""
Services for admin_panel app - Dashboard and Analytics for Administrators
"""

import logging
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from django.db import connection
from datetime import timedelta, datetime, date
from decimal import Decimal
import json

from .models import DashboardMetric, AdminReport, AdminNotification, SystemHealth, AdminAuditLog
from users.models import User
from shipments.models import Shipment
from payments.models import Transaction, Wallet
from trips.models import Trip

logger = logging.getLogger(__name__)


class DashboardService:
    """Service pour le tableau de bord administratif."""
    
    @staticmethod
    def get_dashboard_overview():
        """Récupère la vue d'ensemble complète du tableau de bord."""
        try:
            return {
                'shipments_summary': DashboardService.get_shipments_summary(),
                'payments_summary': DashboardService.get_payments_summary(),
                'commissions_summary': DashboardService.get_commissions_summary(),
                'users_summary': DashboardService.get_users_summary(),
                'financial_summary': DashboardService.get_financial_summary(),
                'performance_summary': DashboardService.get_performance_summary(),
                'real_time_metrics': DashboardService.get_real_time_metrics(),
                'active_alerts': DashboardService.get_active_alerts(),
                'recent_notifications': DashboardService.get_recent_notifications(),
                'charts_data': DashboardService.get_charts_data(),
                'quick_actions': DashboardService.get_quick_actions(),
            }
        except Exception as e:
            logger.error(f"Error getting dashboard overview: {str(e)}")
            return {}
    
    @staticmethod
    def get_shipments_summary():
        """Récupère le résumé des envois."""
        try:
            now = timezone.now()
            today = now.date()
            week_start = today - timedelta(days=today.weekday())
            month_start = today.replace(day=1)
            
            # Statistiques globales
            total_shipments = Shipment.objects.count()
            pending_shipments = Shipment.objects.filter(status='pending').count()
            in_transit_shipments = Shipment.objects.filter(status='in_transit').count()
            delivered_shipments = Shipment.objects.filter(status='delivered').count()
            cancelled_shipments = Shipment.objects.filter(status='cancelled').count()
            
            # Statistiques par période
            shipments_today = Shipment.objects.filter(created_at__date=today).count()
            shipments_this_week = Shipment.objects.filter(created_at__date__gte=week_start).count()
            shipments_this_month = Shipment.objects.filter(created_at__date__gte=month_start).count()
            
            # Calcul des tendances
            last_month_start = month_start - timedelta(days=30)
            last_month_shipments = Shipment.objects.filter(
                created_at__date__gte=last_month_start,
                created_at__date__lt=month_start
            ).count()
            
            if last_month_shipments > 0:
                growth_rate = ((shipments_this_month - last_month_shipments) / last_month_shipments) * 100
            else:
                growth_rate = 0
            
            # Temps de livraison moyen
            delivered_shipments_with_time = Shipment.objects.filter(
                status='delivered',
                delivery_date__isnull=False
            )
            
            if delivered_shipments_with_time.exists():
                avg_delivery_time = delivered_shipments_with_time.aggregate(
                    avg_time=Avg(F('delivery_date') - F('created_at'))
                )['avg_time']
            else:
                avg_delivery_time = timedelta(0)
            
            # Taux de succès
            if total_shipments > 0:
                success_rate = (delivered_shipments / total_shipments) * 100
            else:
                success_rate = 0
            
            # Top destinations
            top_destinations = Shipment.objects.values('destination_city').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            # Répartition par type et statut
            shipments_by_type = dict(Shipment.objects.values_list('package_type').annotate(
                count=Count('id')
            ))
            
            shipments_by_status = dict(Shipment.objects.values_list('status').annotate(
                count=Count('id')
            ))
            
            return {
                'total_shipments': total_shipments,
                'pending_shipments': pending_shipments,
                'in_transit_shipments': in_transit_shipments,
                'delivered_shipments': delivered_shipments,
                'cancelled_shipments': cancelled_shipments,
                'shipments_today': shipments_today,
                'shipments_this_week': shipments_this_week,
                'shipments_this_month': shipments_this_month,
                'growth_rate': round(growth_rate, 2),
                'average_delivery_time': avg_delivery_time if avg_delivery_time else timedelta(0),
                'success_rate': round(success_rate, 2),
                'top_destinations': list(top_destinations),
                'shipments_by_type': shipments_by_type,
                'shipments_by_status': shipments_by_status,
            }
        except Exception as e:
            logger.error(f"Error getting shipments summary: {str(e)}")
            return {}
    
    @staticmethod
    def get_payments_summary():
        """Récupère le résumé des paiements."""
        try:
            now = timezone.now()
            today = now.date()
            week_start = today - timedelta(days=today.weekday())
            month_start = today.replace(day=1)
            
            # Statistiques globales
            total_revenue = Transaction.objects.filter(
                type='payment',
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            total_transactions = Transaction.objects.count()
            successful_payments = Transaction.objects.filter(
                type='payment',
                status='completed'
            ).count()
            
            failed_payments = Transaction.objects.filter(
                type='payment',
                status='failed'
            ).count()
            
            # Statistiques par période
            revenue_today = Transaction.objects.filter(
                type='payment',
                status='completed',
                created_at__date=today
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            revenue_this_week = Transaction.objects.filter(
                type='payment',
                status='completed',
                created_at__date__gte=week_start
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            revenue_this_month = Transaction.objects.filter(
                type='payment',
                status='completed',
                created_at__date__gte=month_start
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Méthodes de paiement
            payments_by_method = dict(Transaction.objects.filter(
                type='payment'
            ).values_list('payment_method').annotate(
                count=Count('id')
            ))
            
            payments_by_status = dict(Transaction.objects.values_list('status').annotate(
                count=Count('id')
            ))
            
            # Tendances
            last_month_start = month_start - timedelta(days=30)
            last_month_revenue = Transaction.objects.filter(
                type='payment',
                status='completed',
                created_at__date__gte=last_month_start,
                created_at__date__lt=month_start
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            if last_month_revenue > 0:
                revenue_growth = ((revenue_this_month - last_month_revenue) / last_month_revenue) * 100
            else:
                revenue_growth = 0
            
            if successful_payments > 0:
                average_transaction_value = total_revenue / successful_payments
            else:
                average_transaction_value = Decimal('0')
            
            # Top clients
            top_clients = Transaction.objects.filter(
                type='payment',
                status='completed'
            ).values('user__username').annotate(
                total_spent=Sum('amount'),
                transaction_count=Count('id')
            ).order_by('-total_spent')[:10]
            
            return {
                'total_revenue': total_revenue,
                'total_transactions': total_transactions,
                'successful_payments': successful_payments,
                'failed_payments': failed_payments,
                'revenue_today': revenue_today,
                'revenue_this_week': revenue_this_week,
                'revenue_this_month': revenue_this_month,
                'payments_by_method': payments_by_method,
                'payments_by_status': payments_by_status,
                'revenue_growth': round(revenue_growth, 2),
                'average_transaction_value': average_transaction_value,
                'top_clients': list(top_clients),
            }
        except Exception as e:
            logger.error(f"Error getting payments summary: {str(e)}")
            return {}
    
    @staticmethod
    def get_commissions_summary():
        """Récupère le résumé des commissions."""
        try:
            now = timezone.now()
            today = now.date()
            week_start = today - timedelta(days=today.weekday())
            month_start = today.replace(day=1)
            
            # Statistiques globales
            total_commissions = Transaction.objects.filter(
                type='commission',
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            total_commissionable_amount = Transaction.objects.filter(
                type='payment',
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            if total_commissionable_amount > 0:
                commission_rate_average = (total_commissions / total_commissionable_amount) * 100
            else:
                commission_rate_average = Decimal('0')
            
            # Statistiques par période
            commissions_today = Transaction.objects.filter(
                type='commission',
                status='completed',
                created_at__date=today
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            commissions_this_week = Transaction.objects.filter(
                type='commission',
                status='completed',
                created_at__date__gte=week_start
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            commissions_this_month = Transaction.objects.filter(
                type='commission',
                status='completed',
                created_at__date__gte=month_start
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Répartition des commissions
            commissions_by_type = dict(Transaction.objects.filter(
                type='commission'
            ).values_list('payment_method').annotate(
                count=Count('id')
            ))
            
            commissions_by_status = dict(Transaction.objects.filter(
                type='commission'
            ).values_list('status').annotate(
                count=Count('id')
            ))
            
            # Top voyageurs (par commissions)
            top_travelers = Transaction.objects.filter(
                type='commission',
                status='completed'
            ).values('user__username').annotate(
                total_commissions=Sum('amount'),
                commission_count=Count('id')
            ).order_by('-total_commissions')[:10]
            
            # Tendances
            last_month_start = month_start - timedelta(days=30)
            last_month_commissions = Transaction.objects.filter(
                type='payment',
                status='completed',
                created_at__date__gte=last_month_start,
                created_at__date__lt=month_start
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            if last_month_commissions > 0:
                commission_growth = ((commissions_this_month - last_month_commissions) / last_month_commissions) * 100
            else:
                commission_growth = 0
            
            # Commission moyenne par envoi
            total_shipments = Shipment.objects.filter(status='delivered').count()
            if total_shipments > 0:
                average_commission_per_shipment = total_commissions / total_shipments
            else:
                average_commission_per_shipment = Decimal('0')
            
            return {
                'total_commissions': total_commissions,
                'total_commissionable_amount': total_commissionable_amount,
                'commission_rate_average': round(commission_rate_average, 2),
                'commissions_today': commissions_today,
                'commissions_this_week': commissions_this_week,
                'commissions_this_month': commissions_this_month,
                'commissions_by_type': commissions_by_type,
                'commissions_by_status': commissions_by_status,
                'top_travelers': list(top_travelers),
                'commission_growth': round(commission_growth, 2),
                'average_commission_per_shipment': average_commission_per_shipment,
            }
        except Exception as e:
            logger.error(f"Error getting commissions summary: {str(e)}")
            return {}
    
    @staticmethod
    def get_users_summary():
        """Récupère le résumé des utilisateurs."""
        try:
            now = timezone.now()
            today = now.date()
            week_start = today - timedelta(days=today.weekday())
            month_start = today.replace(day=1)
            
            # Statistiques globales
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            new_users_today = User.objects.filter(date_joined__date=today).count()
            new_users_this_week = User.objects.filter(date_joined__date__gte=week_start).count()
            new_users_this_month = User.objects.filter(date_joined__date__gte=month_start).count()
            
            # Répartition par rôle
            users_by_role = dict(User.objects.values_list('role').annotate(
                count=Count('id')
            ))
            
            users_by_status = {
                'active': User.objects.filter(is_active=True).count(),
                'inactive': User.objects.filter(is_active=False).count(),
            }
            
            # Répartition par statut de vérification
            users_by_verification = {
                'verified': User.objects.filter(is_document_verified=True).count(),
                'unverified': User.objects.filter(is_document_verified=False).count(),
            }
            
            # Top utilisateurs
            top_senders = User.objects.filter(role='sender').annotate(
                shipment_count=Count('sent_shipments')
            ).order_by('-shipment_count')[:10]
            
            top_travelers = User.objects.filter(role='traveler').annotate(
                trip_count=Count('trips')
            ).order_by('-trip_count')[:10]
            
            # Tendances
            last_month_start = month_start - timedelta(days=30)
            last_month_users = User.objects.filter(
                date_joined__date__gte=last_month_start,
                date_joined__date__lt=month_start
            ).count()
            
            if last_month_users > 0:
                user_growth_rate = ((new_users_this_month - last_month_users) / last_month_users) * 100
            else:
                user_growth_rate = 0
            
            if total_users > 0:
                active_user_percentage = (active_users / total_users) * 100
            else:
                active_user_percentage = 0
            
            # Géographie (simulation - fields don't exist in User model)
            users_by_country = {'Algeria': total_users}  # Placeholder
            
            users_by_city = {'Algiers': total_users // 2, 'Oran': total_users // 4}  # Placeholder
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'new_users_today': new_users_today,
                'new_users_this_week': new_users_this_week,
                'new_users_this_month': new_users_this_month,
                'users_by_role': users_by_role,
                'users_by_status': users_by_status,
                'users_by_verification': users_by_verification,
                'top_senders': list(top_senders.values('username', 'shipment_count')),
                'top_travelers': list(top_travelers.values('username', 'trip_count')),
                'user_growth_rate': round(user_growth_rate, 2),
                'active_user_percentage': round(active_user_percentage, 2),
                'users_by_country': users_by_country,
                'users_by_city': users_by_city,
            }
        except Exception as e:
            logger.error(f"Error getting users summary: {str(e)}")
            return {}
    
    @staticmethod
    def get_financial_summary():
        """Récupère le résumé financier."""
        try:
            now = timezone.now()
            today = now.date()
            month_start = today.replace(day=1)
            
            # Revenus
            total_revenue = Transaction.objects.filter(
                type='payment',
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Dépenses (simulation - à adapter selon votre modèle)
            total_expenses = Decimal('0')  # À implémenter selon votre modèle de dépenses
            
            # Profit net
            net_profit = total_revenue - total_expenses
            
            # Marge de profit
            if total_revenue > 0:
                profit_margin = (net_profit / total_revenue) * 100
            else:
                profit_margin = 0
            
            # Revenus par source
            revenue_by_source = {
                'shipments': total_revenue,
                'commissions': Transaction.objects.filter(
                    type='commission',
                    status='completed'
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0'),
            }
            
            # Revenus par période (12 derniers mois)
            revenue_by_period = {}
            for i in range(12):
                month = month_start - timedelta(days=30*i)
                month_end = month + timedelta(days=30)
                month_revenue = Transaction.objects.filter(
                    type='payment',
                    status='completed',
                    created_at__date__gte=month,
                    created_at__date__lt=month_end
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                revenue_by_period[month.strftime('%Y-%m')] = month_revenue
            
            # Trésorerie
            cash_flow = {
                'inflow': total_revenue,
                'outflow': total_expenses,
                'net_flow': net_profit,
            }
            
            # Paiements en attente
            outstanding_payments = Transaction.objects.filter(
                type='payment',
                status='pending'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            return {
                'total_revenue': total_revenue,
                'total_expenses': total_expenses,
                'net_profit': net_profit,
                'profit_margin': round(profit_margin, 2),
                'revenue_by_source': revenue_by_source,
                'revenue_by_period': revenue_by_period,
                'expenses_by_category': {},  # À implémenter
                'expenses_by_period': {},    # À implémenter
                'cash_flow': cash_flow,
                'outstanding_payments': outstanding_payments,
                'revenue_trend': [],  # À implémenter
                'profit_trend': [],   # À implémenter
            }
        except Exception as e:
            logger.error(f"Error getting financial summary: {str(e)}")
            return {}
    
    @staticmethod
    def get_performance_summary():
        """Récupère le résumé des performances."""
        try:
            # Métriques de performance système (simulation)
            system_uptime = Decimal('99.5')  # À implémenter avec monitoring réel
            average_response_time = timedelta(milliseconds=150)  # À implémenter
            error_rate = Decimal('0.1')  # À implémenter
            
            # Performance des envois
            total_shipments = Shipment.objects.count()
            delivered_shipments = Shipment.objects.filter(status='delivered').count()
            
            if total_shipments > 0:
                delivery_success_rate = (delivered_shipments / total_shipments) * 100
            else:
                delivery_success_rate = 0
            
            # Temps de livraison moyen
            delivered_shipments_with_time = Shipment.objects.filter(
                status='delivered',
                delivery_date__isnull=False
            )
            
            if delivered_shipments_with_time.exists():
                avg_delivery_time = delivered_shipments_with_time.aggregate(
                    avg_time=Avg(F('delivery_date') - F('created_at'))
                )['avg_time']
            else:
                avg_delivery_time = timedelta(0)
            
            # Score de satisfaction client (simulation)
            customer_satisfaction_score = Decimal('4.2')  # À implémenter avec système de notation
            
            # Performance des utilisateurs
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            
            if total_users > 0:
                user_engagement_rate = (active_users / total_users) * 100
            else:
                user_engagement_rate = 0
            
            user_retention_rate = Decimal('85.0')  # À implémenter avec analyse de rétention
            
            # Métriques techniques
            database_performance = {
                'query_count': 1000,  # À implémenter
                'slow_queries': 5,    # À implémenter
                'connection_pool': 80, # À implémenter
            }
            
            api_performance = {
                'requests_per_minute': 150,  # À implémenter
                'average_response_time': 150, # en millisecondes, à implémenter
                'error_rate': 0.1,           # À implémenter
            }
            
            cache_performance = {
                'hit_rate': 85.0,     # À implémenter
                'miss_rate': 15.0,    # À implémenter
                'eviction_rate': 5.0, # À implémenter
            }
            
            return {
                'system_uptime': system_uptime,
                'average_response_time': average_response_time,
                'error_rate': error_rate,
                'delivery_success_rate': round(delivery_success_rate, 2),
                'average_delivery_time': avg_delivery_time if avg_delivery_time else timedelta(0),
                'customer_satisfaction_score': customer_satisfaction_score,
                'user_engagement_rate': round(user_engagement_rate, 2),
                'user_retention_rate': user_retention_rate,
                'database_performance': database_performance,
                'api_performance': api_performance,
                'cache_performance': cache_performance,
            }
        except Exception as e:
            logger.error(f"Error getting performance summary: {str(e)}")
            return {}
    
    @staticmethod
    def get_real_time_metrics():
        """Récupère les métriques en temps réel."""
        try:
            now = timezone.now()
            today = now.date()
            
            # Envois en temps réel
            active_shipments = Shipment.objects.filter(status='in_transit').count()
            pending_shipments = Shipment.objects.filter(status='pending').count()
            
            # Paiements en temps réel
            pending_payments = Transaction.objects.filter(
                type='payment',
                status='pending'
            ).count()
            
            # Utilisateurs en ligne (simulation)
            online_users = User.objects.filter(
                last_login__gte=now - timedelta(minutes=15)
            ).count()
            
            # Transactions récentes
            recent_transactions = Transaction.objects.filter(
                created_at__gte=now - timedelta(hours=1)
            ).count()
            
            return {
                'active_shipments': active_shipments,
                'pending_shipments': pending_shipments,
                'pending_payments': pending_payments,
                'online_users': online_users,
                'recent_transactions': recent_transactions,
                'last_updated': now.isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting real-time metrics: {str(e)}")
            return {}
    
    @staticmethod
    def get_active_alerts():
        """Récupère les alertes actives."""
        try:
            alerts = []
            
            # Alerte pour envois en attente
            pending_shipments = Shipment.objects.filter(status='pending').count()
            if pending_shipments > 10:
                alerts.append({
                    'type': 'warning',
                    'title': 'Envois en attente',
                    'message': f'{pending_shipments} envois sont en attente de traitement',
                    'action_url': '/admin/shipments/',
                    'priority': 'medium'
                })
            
            # Alerte pour paiements échoués
            failed_payments = Transaction.objects.filter(
                type='payment',
                status='failed'
            ).count()
            if failed_payments > 5:
                alerts.append({
                    'type': 'error',
                    'title': 'Paiements échoués',
                    'message': f'{failed_payments} paiements ont échoué',
                    'action_url': '/admin/payments/',
                    'priority': 'high'
                })
            
            # Alerte pour système
            if SystemHealth.objects.filter(status='critical').exists():
                alerts.append({
                    'type': 'critical',
                    'title': 'Système critique',
                    'message': 'Un ou plusieurs services sont en état critique',
                    'action_url': '/admin/system-health/',
                    'priority': 'urgent'
                })
            
            return alerts
        except Exception as e:
            logger.error(f"Error getting active alerts: {str(e)}")
            return []
    
    @staticmethod
    def get_recent_notifications():
        """Récupère les notifications récentes."""
        try:
            return list(AdminNotification.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).values('title', 'message', 'notification_type', 'priority', 'created_at')[:10])
        except Exception as e:
            logger.error(f"Error getting recent notifications: {str(e)}")
            return []
    
    @staticmethod
    def get_charts_data():
        """Récupère les données pour les graphiques."""
        try:
            now = timezone.now()
            month_start = now.replace(day=1)
            
            # Données pour le graphique des envois (12 derniers mois)
            shipments_chart = []
            for i in range(12):
                month = month_start - timedelta(days=30*i)
                month_end = month + timedelta(days=30)
                count = Shipment.objects.filter(
                    created_at__date__gte=month,
                    created_at__date__lt=month_end
                ).count()
                shipments_chart.append({
                    'month': month.strftime('%Y-%m'),
                    'count': count
                })
            
            # Données pour le graphique des revenus
            revenue_chart = []
            for i in range(12):
                month = month_start - timedelta(days=30*i)
                month_end = month + timedelta(days=30)
                revenue = Transaction.objects.filter(
                    type='payment',
                    status='completed',
                    created_at__date__gte=month,
                    created_at__date__lt=month_end
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                revenue_chart.append({
                    'month': month.strftime('%Y-%m'),
                    'revenue': float(revenue)
                })
            
            # Données pour le graphique des utilisateurs
            users_chart = []
            for i in range(12):
                month = month_start - timedelta(days=30*i)
                month_end = month + timedelta(days=30)
                count = User.objects.filter(
                    date_joined__date__gte=month,
                    date_joined__date__lt=month_end
                ).count()
                users_chart.append({
                    'month': month.strftime('%Y-%m'),
                    'count': count
                })
            
            return {
                'shipments_chart': shipments_chart,
                'revenue_chart': revenue_chart,
                'users_chart': users_chart,
            }
        except Exception as e:
            logger.error(f"Error getting charts data: {str(e)}")
            return {}
    
    @staticmethod
    def get_quick_actions():
        """Récupère les actions rapides disponibles."""
        try:
            return [
                {
                    'title': 'Créer un envoi',
                    'description': 'Créer un nouvel envoi manuellement',
                    'action_url': '/admin/shipments/shipment/add/',
                    'icon': 'add_shopping_cart',
                    'permission': 'shipments.add_shipment'
                },
                {
                    'title': 'Gérer les paiements',
                    'description': 'Voir et gérer tous les paiements',
                    'action_url': '/admin/payments/',
                    'icon': 'payment',
                    'permission': 'payments.view_transaction'
                },
                {
                    'title': 'Rapport financier',
                    'description': 'Générer un rapport financier',
                    'action_url': '/admin/reports/financial/',
                    'icon': 'assessment',
                    'permission': 'admin_panel.view_adminreport'
                },
                {
                    'title': 'Gérer les utilisateurs',
                    'description': 'Gérer les comptes utilisateurs',
                    'action_url': '/admin/users/',
                    'icon': 'people',
                    'permission': 'users.view_user'
                },
                {
                    'title': 'Système de santé',
                    'description': 'Vérifier l\'état du système',
                    'action_url': '/admin/system-health/',
                    'icon': 'health_and_safety',
                    'permission': 'admin_panel.view_systemhealth'
                },
            ]
        except Exception as e:
            logger.error(f"Error getting quick actions: {str(e)}")
            return []


class ReportService:
    """Service pour la génération de rapports."""
    
    @staticmethod
    def generate_report(report_type, format='json', filters=None, parameters=None):
        """Génère un rapport selon le type spécifié."""
        try:
            if report_type == 'shipments_summary':
                data = DashboardService.get_shipments_summary()
            elif report_type == 'payments_summary':
                data = DashboardService.get_payments_summary()
            elif report_type == 'commissions_summary':
                data = DashboardService.get_commissions_summary()
            elif report_type == 'users_summary':
                data = DashboardService.get_users_summary()
            elif report_type == 'financial_summary':
                data = DashboardService.get_financial_summary()
            elif report_type == 'performance_summary':
                data = DashboardService.get_performance_summary()
            else:
                data = {}
            
            # Nettoyer les paramètres pour la sérialisation JSON
            clean_parameters = {}
            if parameters:
                for key, value in parameters.items():
                    if key == 'user':
                        # Stocker l'ID de l'utilisateur au lieu de l'objet User
                        clean_parameters[key] = value.id if hasattr(value, 'id') else str(value)
                    else:
                        # Vérifier si la valeur est JSON sérialisable
                        try:
                            json.dumps(value)
                            clean_parameters[key] = value
                        except (TypeError, ValueError):
                            # Si non sérialisable, convertir en string
                            clean_parameters[key] = str(value)
            
            # Nettoyer les données du rapport pour la sérialisation JSON
            def clean_for_json(obj):
                """Nettoie un objet pour la sérialisation JSON."""
                if isinstance(obj, dict):
                    return {key: clean_for_json(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [clean_for_json(item) for item in obj]
                elif isinstance(obj, (Decimal, datetime, date)):
                    return str(obj)
                elif hasattr(obj, 'isoformat'):  # Pour les objets datetime
                    return obj.isoformat()
                else:
                    try:
                        json.dumps(obj)
                        return obj
                    except (TypeError, ValueError):
                        return str(obj)
            
            clean_result_data = clean_for_json(data)
            
            # Créer l'enregistrement du rapport
            report = AdminReport.objects.create(
                name=f"Rapport {report_type} - {timezone.now().strftime('%Y-%m-%d %H:%M')}",
                report_type=report_type,
                format=format,
                parameters=clean_parameters,
                filters=filters or {},
                result_data=clean_result_data,
                generated_by=parameters.get('user') if parameters else None,
            )
            
            return report
        except Exception as e:
            logger.error(f"Error generating report {report_type}: {str(e)}")
            return None


class NotificationService:
    """Service pour la gestion des notifications administratives."""
    
    @staticmethod
    def create_notification(title, message, notification_type='info', priority='normal', 
                          recipients=None, is_broadcast=False, action_url='', action_text=''):
        """Crée une nouvelle notification administrative."""
        try:
            notification = AdminNotification.objects.create(
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                is_broadcast=is_broadcast,
                action_url=action_url,
                action_text=action_text,
            )
            
            if recipients:
                notification.recipients.set(recipients)
            
            return notification
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            return None
    
    @staticmethod
    def mark_as_read(notification_id, user):
        """Marque une notification comme lue."""
        try:
            notification = AdminNotification.objects.get(id=notification_id)
            notification.read_by.add(user)
            notification.is_read = True
            notification.save()
            return True
        except AdminNotification.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return False


class SystemHealthService:
    """Service pour la surveillance de la santé du système."""
    
    @staticmethod
    def check_system_health():
        """Vérifie la santé générale du système."""
        try:
            health_checks = {}
            
            # Vérification de la base de données
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                health_checks['database'] = {
                    'status': 'healthy',
                    'response_time': 50,  # en millisecondes
                    'uptime_percentage': Decimal('99.9'),
                    'error_count': 0,
                    'details': {'connection': 'OK', 'queries': 'OK'}
                }
            except Exception as e:
                health_checks['database'] = {
                    'status': 'critical',
                    'response_time': None,
                    'uptime_percentage': Decimal('0.0'),
                    'error_count': 1,
                    'details': {'error': str(e)}
                }
            
            # Vérification des modèles principaux
            try:
                user_count = User.objects.count()
                shipment_count = Shipment.objects.count()
                transaction_count = Transaction.objects.count()
                
                health_checks['models'] = {
                    'status': 'healthy',
                    'response_time': 100,  # en millisecondes
                    'uptime_percentage': Decimal('99.9'),
                    'error_count': 0,
                    'details': {
                        'users': user_count,
                        'shipments': shipment_count,
                        'transactions': transaction_count
                    }
                }
            except Exception as e:
                health_checks['models'] = {
                    'status': 'critical',
                    'response_time': None,
                    'uptime_percentage': Decimal('0.0'),
                    'error_count': 1,
                    'details': {'error': str(e)}
                }
            
            # Mise à jour des enregistrements de santé
            for service_name, health_data in health_checks.items():
                SystemHealth.objects.update_or_create(
                    service_name=service_name,
                    defaults=health_data
                )
            
            return health_checks
        except Exception as e:
            logger.error(f"Error checking system health: {str(e)}")
            return {}


class AuditService:
    """Service pour la gestion des logs d'audit."""
    
    @staticmethod
    def log_action(user, action, model_name='', object_id='', changes=None, 
                  ip_address=None, user_agent=None, session_id=None, metadata=None):
        """Enregistre une action dans les logs d'audit."""
        try:
            AdminAuditLog.objects.create(
                user=user,
                action=action,
                model_name=model_name,
                object_id=object_id,
                changes=changes or {},
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                metadata=metadata or {},
            )
            return True
        except Exception as e:
            logger.error(f"Error logging audit action: {str(e)}")
            return False
