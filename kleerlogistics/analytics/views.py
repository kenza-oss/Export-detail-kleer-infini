"""
Views for analytics app - Dashboard analytics and statistics
"""

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncDate, TruncMonth
import random
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import AnalyticsEvent, DashboardMetric
from .serializers import (
    AnalyticsEventSerializer, DashboardMetricSerializer,
    DashboardAnalyticsSerializer, ShipmentAnalyticsSerializer
)
from config.swagger_config import (
    analytics_dashboard_schema, analytics_shipment_schema,
    analytics_trip_schema, analytics_financial_schema,
    analytics_event_schema
)
from config.swagger_examples import (
    ANALYTICS_DASHBOARD_EXAMPLE, ANALYTICS_SHIPMENT_EXAMPLE,
    ANALYTICS_TRIP_EXAMPLE, ANALYTICS_FINANCIAL_EXAMPLE,
    ANALYTICS_EVENT_EXAMPLE
)


class DashboardAnalyticsView(APIView):
    """Vue pour les analytics du tableau de bord."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer les analytics du tableau de bord",
        manual_parameters=[
            openapi.Parameter(
                'date_from',
                openapi.IN_QUERY,
                description="Date de début (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            ),
            openapi.Parameter(
                'date_to',
                openapi.IN_QUERY,
                description="Date de fin (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Analytics du tableau de bord",
                examples={"application/json": ANALYTICS_DASHBOARD_EXAMPLE["response"]}
            )
        }
    )
    def get(self, request):
        """Récupérer les analytics du tableau de bord."""
        user = request.user
        
        # Statistiques générales
        general_stats = self.get_general_stats(user)
        
        # Statistiques des envois
        shipment_stats = self.get_shipment_stats(user)
        
        # Statistiques des trajets
        trip_stats = self.get_trip_stats(user)
        
        # Statistiques financières
        financial_stats = self.get_financial_stats(user)
        
        # Graphiques et tendances
        charts_data = self.get_charts_data(user)
        
        analytics = {
            'general': general_stats,
            'shipments': shipment_stats,
            'trips': trip_stats,
            'financial': financial_stats,
            'charts': charts_data
        }
        
        return Response({
            'success': True,
            'analytics': analytics
        })
    
    def get_general_stats(self, user):
        """Obtenir les statistiques générales."""
        from users.models import User
        from shipments.models import Shipment
        from trips.models import Trip
        
        total_users = User.objects.count()
        total_shipments = Shipment.objects.count()
        total_trips = Trip.objects.count()
        
        return {
            'total_users': total_users,
            'total_shipments': total_shipments,
            'total_trips': total_trips,
            'active_shipments': Shipment.objects.filter(status='active').count(),
            'completed_shipments': Shipment.objects.filter(status='delivered').count(),
            'active_trips': Trip.objects.filter(status='active').count(),
            'completed_trips': Trip.objects.filter(status='completed').count()
        }
    
    def get_shipment_stats(self, user):
        """Obtenir les statistiques des envois."""
        from shipments.models import Shipment
        
        user_shipments = Shipment.objects.filter(user=user)
        
        return {
            'total_shipments': user_shipments.count(),
            'pending_shipments': user_shipments.filter(status='pending').count(),
            'in_transit_shipments': user_shipments.filter(status='in_transit').count(),
            'delivered_shipments': user_shipments.filter(status='delivered').count(),
            'cancelled_shipments': user_shipments.filter(status='cancelled').count(),
            'total_revenue': user_shipments.aggregate(total=Sum('shipping_cost'))['total'] or 0,
            'average_delivery_time': self.calculate_average_delivery_time(user_shipments)
        }
    
    def get_trip_stats(self, user):
        """Obtenir les statistiques des trajets."""
        from trips.models import Trip
        
        user_trips = Trip.objects.filter(traveler=user)
        
        return {
            'total_trips': user_trips.count(),
            'active_trips': user_trips.filter(status='active').count(),
            'completed_trips': user_trips.filter(status='completed').count(),
            'cancelled_trips': user_trips.filter(status='cancelled').count(),
            'total_earnings': user_trips.aggregate(total=Sum('earnings'))['total'] or 0,
            'average_rating': user_trips.aggregate(avg=Avg('rating'))['avg'] or 0
        }
    
    def get_financial_stats(self, user):
        """Obtenir les statistiques financières."""
        from payments.models import Transaction, Wallet
        
        try:
            wallet = Wallet.objects.get(user=user)
            balance = wallet.balance
        except Wallet.DoesNotExist:
            balance = 0
        
        user_transactions = Transaction.objects.filter(user=user)
        
        return {
            'current_balance': balance,
            'total_deposits': user_transactions.filter(transaction_type='deposit').aggregate(total=Sum('amount'))['total'] or 0,
            'total_withdrawals': user_transactions.filter(transaction_type='withdrawal').aggregate(total=Sum('amount'))['total'] or 0,
            'total_transfers': user_transactions.filter(transaction_type__in=['transfer_in', 'transfer_out']).aggregate(total=Sum('amount'))['total'] or 0,
            'monthly_revenue': self.get_monthly_revenue(user_transactions)
        }
    
    def get_charts_data(self, user):
        """Obtenir les données pour les graphiques."""
        from shipments.models import Shipment
        from trips.models import Trip
        
        # Envois par mois
        shipments_by_month = Shipment.objects.filter(user=user).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        # Trajets par mois
        trips_by_month = Trip.objects.filter(traveler=user).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        # Statuts des envois
        shipment_statuses = Shipment.objects.filter(user=user).values('status').annotate(
            count=Count('id')
        )
        
        return {
            'shipments_by_month': list(shipments_by_month),
            'trips_by_month': list(trips_by_month),
            'shipment_statuses': list(shipment_statuses)
        }
    
    def calculate_average_delivery_time(self, shipments):
        """Calculer le temps de livraison moyen."""
        delivered_shipments = shipments.filter(
            status='delivered',
            delivery_date__isnull=False,
            created_at__isnull=False
        )
        
        if delivered_shipments.count() == 0:
            return 0
        
        total_days = 0
        for shipment in delivered_shipments:
            delivery_time = (shipment.delivery_date - shipment.created_at).days
            total_days += delivery_time
        
        return total_days / delivered_shipments.count()
    
    def get_monthly_revenue(self, transactions):
        """Obtenir les revenus mensuels."""
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        monthly_transactions = transactions.filter(
            created_at__month=current_month,
            created_at__year=current_year,
            transaction_type='shipment_payment'
        )
        
        return monthly_transactions.aggregate(total=Sum('amount'))['total'] or 0


class ShipmentAnalyticsView(APIView):
    """Vue pour les analytics des envois."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer les analytics des expéditions",
        manual_parameters=[
            openapi.Parameter(
                'date_from',
                openapi.IN_QUERY,
                description="Date de début (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            ),
            openapi.Parameter(
                'date_to',
                openapi.IN_QUERY,
                description="Date de fin (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Analytics des expéditions",
                examples={"application/json": ANALYTICS_SHIPMENT_EXAMPLE["response"]}
            )
        }
    )
    def get(self, request):
        """Récupérer les analytics des envois."""
        from shipments.models import Shipment
        
        user_shipments = Shipment.objects.filter(user=request.user)
        
        analytics = {
            'total_shipments': user_shipments.count(),
            'shipments_by_status': self.get_shipments_by_status(user_shipments),
            'shipments_by_month': self.get_shipments_by_month(user_shipments),
            'top_destinations': self.get_top_destinations(user_shipments),
            'revenue_analysis': self.get_revenue_analysis(user_shipments),
            'delivery_performance': self.get_delivery_performance(user_shipments)
        }
        
        return Response({
            'success': True,
            'analytics': analytics
        })
    
    def get_shipments_by_status(self, shipments):
        """Obtenir les envois par statut."""
        return list(shipments.values('status').annotate(count=Count('id')))
    
    def get_shipments_by_month(self, shipments):
        """Obtenir les envois par mois."""
        return list(shipments.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month'))
    
    def get_top_destinations(self, shipments):
        """Obtenir les destinations les plus populaires."""
        return list(shipments.values('destination').annotate(
            count=Count('id')
        ).order_by('-count')[:10])
    
    def get_revenue_analysis(self, shipments):
        """Obtenir l'analyse des revenus."""
        return {
            'total_revenue': shipments.aggregate(total=Sum('shipping_cost'))['total'] or 0,
            'average_revenue': shipments.aggregate(avg=Avg('shipping_cost'))['avg'] or 0,
            'monthly_revenue': self.get_monthly_revenue(shipments)
        }
    
    def get_delivery_performance(self, shipments):
        """Obtenir les performances de livraison."""
        delivered_shipments = shipments.filter(status='delivered')
        
        if delivered_shipments.count() == 0:
            return {
                'average_delivery_time': 0,
                'on_time_deliveries': 0,
                'late_deliveries': 0
            }
        
        total_delivery_time = 0
        on_time_count = 0
        late_count = 0
        
        for shipment in delivered_shipments:
            if shipment.delivery_date and shipment.created_at:
                delivery_time = (shipment.delivery_date - shipment.created_at).days
                total_delivery_time += delivery_time
                
                # Considérer comme à temps si livré en moins de 7 jours
                if delivery_time <= 7:
                    on_time_count += 1
                else:
                    late_count += 1
        
        return {
            'average_delivery_time': total_delivery_time / delivered_shipments.count(),
            'on_time_deliveries': on_time_count,
            'late_deliveries': late_count
        }
    
    def get_monthly_revenue(self, shipments):
        """Obtenir les revenus mensuels."""
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        monthly_shipments = shipments.filter(
            created_at__month=current_month,
            created_at__year=current_year
        )
        
        return monthly_shipments.aggregate(total=Sum('shipping_cost'))['total'] or 0


class TripAnalyticsView(APIView):
    """Vue pour les analytics des trajets."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer les analytics des voyages",
        manual_parameters=[
            openapi.Parameter(
                'date_from',
                openapi.IN_QUERY,
                description="Date de début (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            ),
            openapi.Parameter(
                'date_to',
                openapi.IN_QUERY,
                description="Date de fin (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Analytics des voyages",
                examples={"application/json": ANALYTICS_TRIP_EXAMPLE["response"]}
            )
        }
    )
    def get(self, request):
        """Récupérer les analytics des trajets."""
        from trips.models import Trip
        
        user_trips = Trip.objects.filter(traveler=request.user)
        
        analytics = {
            'total_trips': user_trips.count(),
            'trips_by_status': self.get_trips_by_status(user_trips),
            'trips_by_month': self.get_trips_by_month(user_trips),
            'top_routes': self.get_top_routes(user_trips),
            'earnings_analysis': self.get_earnings_analysis(user_trips),
            'performance_metrics': self.get_performance_metrics(user_trips)
        }
        
        return Response({
            'success': True,
            'analytics': analytics
        })
    
    def get_trips_by_status(self, trips):
        """Obtenir les trajets par statut."""
        return list(trips.values('status').annotate(count=Count('id')))
    
    def get_trips_by_month(self, trips):
        """Obtenir les trajets par mois."""
        return list(trips.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month'))
    
    def get_top_routes(self, trips):
        """Obtenir les routes les plus populaires."""
        routes = {}
        for trip in trips:
            route = f"{trip.origin} → {trip.destination}"
            routes[route] = routes.get(route, 0) + 1
        
        return sorted(routes.items(), key=lambda x: x[1], reverse=True)[:10]
    
    def get_earnings_analysis(self, trips):
        """Obtenir l'analyse des gains."""
        return {
            'total_earnings': trips.aggregate(total=Sum('earnings'))['total'] or 0,
            'average_earnings': trips.aggregate(avg=Avg('earnings'))['avg'] or 0,
            'monthly_earnings': self.get_monthly_earnings(trips)
        }
    
    def get_performance_metrics(self, trips):
        """Obtenir les métriques de performance."""
        completed_trips = trips.filter(status='completed')
        
        return {
            'completion_rate': (completed_trips.count() / trips.count()) * 100 if trips.count() > 0 else 0,
            'average_rating': completed_trips.aggregate(avg=Avg('rating'))['avg'] or 0,
            'total_distance': trips.aggregate(total=Sum('distance'))['total'] or 0
        }
    
    def get_monthly_earnings(self, trips):
        """Obtenir les gains mensuels."""
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        monthly_trips = trips.filter(
            created_at__month=current_month,
            created_at__year=current_year
        )
        
        return monthly_trips.aggregate(total=Sum('earnings'))['total'] or 0


class FinancialAnalyticsView(APIView):
    """Vue pour les analytics financiers."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Récupérer les analytics financiers",
        manual_parameters=[
            openapi.Parameter(
                'date_from',
                openapi.IN_QUERY,
                description="Date de début (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            ),
            openapi.Parameter(
                'date_to',
                openapi.IN_QUERY,
                description="Date de fin (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Analytics financiers",
                examples={"application/json": ANALYTICS_FINANCIAL_EXAMPLE["response"]}
            )
        }
    )
    def get(self, request):
        """Récupérer les analytics financiers."""
        from payments.models import Transaction, Wallet
        
        try:
            wallet = Wallet.objects.get(user=request.user)
            balance = wallet.balance
        except Wallet.DoesNotExist:
            balance = 0
        
        user_transactions = Transaction.objects.filter(user=request.user)
        
        analytics = {
            'current_balance': balance,
            'transaction_summary': self.get_transaction_summary(user_transactions),
            'monthly_transactions': self.get_monthly_transactions(user_transactions),
            'payment_methods': self.get_payment_methods(user_transactions),
            'cash_flow': self.get_cash_flow(user_transactions)
        }
        
        return Response({
            'success': True,
            'analytics': analytics
        })
    
    def get_transaction_summary(self, transactions):
        """Obtenir le résumé des transactions."""
        return {
            'total_transactions': transactions.count(),
            'total_deposits': transactions.filter(transaction_type='deposit').aggregate(total=Sum('amount'))['total'] or 0,
            'total_withdrawals': transactions.filter(transaction_type='withdrawal').aggregate(total=Sum('amount'))['total'] or 0,
            'total_transfers': transactions.filter(transaction_type__in=['transfer_in', 'transfer_out']).aggregate(total=Sum('amount'))['total'] or 0,
            'total_spent': transactions.filter(transaction_type='shipment_payment').aggregate(total=Sum('amount'))['total'] or 0,
            'total_earned': transactions.filter(transaction_type='commission').aggregate(total=Sum('amount'))['total'] or 0
        }
    
    def get_monthly_transactions(self, transactions):
        """Obtenir les transactions mensuelles."""
        return list(transactions.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('month'))
    
    def get_payment_methods(self, transactions):
        """Obtenir les méthodes de paiement utilisées."""
        return list(transactions.values('payment_method').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ))
    
    def get_cash_flow(self, transactions):
        """Obtenir le flux de trésorerie."""
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        monthly_transactions = transactions.filter(
            created_at__month=current_month,
            created_at__year=current_year
        )
        
        inflows = monthly_transactions.filter(
            transaction_type__in=['deposit', 'transfer_in', 'commission']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        outflows = monthly_transactions.filter(
            transaction_type__in=['withdrawal', 'transfer_out', 'shipment_payment']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return {
            'inflows': inflows,
            'outflows': outflows,
            'net_flow': inflows - outflows
        }


class AnalyticsEventView(APIView):
    """Vue pour les événements d'analytics."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Enregistrer un événement analytics",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'event_type': openapi.Schema(type=openapi.TYPE_STRING),
                'event_data': openapi.Schema(type=openapi.TYPE_OBJECT),
                'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME)
            },
            required=['event_type', 'event_data']
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Événement enregistré",
                examples={"application/json": ANALYTICS_EVENT_EXAMPLE["response"]}
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Erreur de validation",
                examples={"application/json": {
                    "success": False,
                    "message": "Type d'événement requis"
                }}
            )
        }
    )
    def post(self, request):
        """Enregistrer un événement d'analytics."""
        event_type = request.data.get('event_type')
        event_data = request.data.get('event_data', {})
        
        if not event_type:
            return Response({
                'success': False,
                'message': 'Type d\'événement requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer l'événement d'analytics
        event = AnalyticsEvent.objects.create(
            user=request.user,
            event_type=event_type,
            event_data=event_data
        )
        
        return Response({
            'success': True,
            'message': 'Événement enregistré',
            'event_id': event.id
        })


# Views pour l'administration
class AdminAnalyticsView(APIView):
    """Vue admin pour les analytics globaux."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Récupérer les analytics globaux."""
        from users.models import User
        from shipments.models import Shipment
        from trips.models import Trip
        from payments.models import Transaction
        
        analytics = {
            'users': {
                'total_users': User.objects.count(),
                'active_users': User.objects.filter(is_active=True).count(),
                'new_users_this_month': User.objects.filter(
                    date_joined__month=timezone.now().month
                ).count()
            },
            'shipments': {
                'total_shipments': Shipment.objects.count(),
                'pending_shipments': Shipment.objects.filter(status='pending').count(),
                'delivered_shipments': Shipment.objects.filter(status='delivered').count(),
                'total_revenue': Shipment.objects.aggregate(total=Sum('shipping_cost'))['total'] or 0
            },
            'trips': {
                'total_trips': Trip.objects.count(),
                'active_trips': Trip.objects.filter(status='active').count(),
                'completed_trips': Trip.objects.filter(status='completed').count()
            },
            'transactions': {
                'total_transactions': Transaction.objects.count(),
                'total_volume': Transaction.objects.aggregate(total=Sum('amount'))['total'] or 0
            }
        }
        
        return Response({
            'success': True,
            'analytics': analytics
        })
