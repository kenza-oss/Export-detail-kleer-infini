"""
Services for matching app - Automatic matching, notifications and OTP services

"""

from django.db import transaction, models
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
import random
import logging

from .models import Match, MatchingPreferences, MatchingRule
from shipments.models import Shipment
from trips.models import Trip
from users.models import User

logger = logging.getLogger(__name__)


class AutomaticMatchingService:
    """Service pour le matching automatique"""
    
    @staticmethod
    def find_matches_for_shipment(shipment, limit=10):
        """Trouve les meilleurs matches pour un envoi."""
        try:
            # Récupérer les règles de matching actives
            rules = MatchingRule.objects.filter(is_active=True).first()
            if not rules:
                rules = MatchingRule.objects.create(
                    name="Règle par défaut",
                    description="Règle de matching par défaut",
                    is_active=True
                )
            
            # Critères de base
            compatible_trips = Trip.objects.filter(
                status='active',
                remaining_weight__gte=shipment.weight,
                remaining_packages__gt=0,
                departure_date__gte=timezone.now().date()
            ).exclude(traveler=shipment.sender)
            
            # Filtres géographiques
            origin_matches = Q(origin_city__icontains=shipment.origin_city)
            destination_matches = Q(destination_city__icontains=shipment.destination_city)
            
            # Correspondances partielles pour plus de flexibilité
            if len(shipment.origin_city) > 3:
                origin_matches |= Q(origin_city__icontains=shipment.origin_city[:3])
            if len(shipment.destination_city) > 3:
                destination_matches |= Q(destination_city__icontains=shipment.destination_city[:3])
            
            compatible_trips = compatible_trips.filter(origin_matches & destination_matches)
            
            # Filtres de type de colis
            if shipment.package_type:
                compatible_trips = compatible_trips.filter(
                    accepted_package_types__contains=shipment.package_type
                )
            
            # Filtre de fragilité
            if shipment.is_fragile:
                compatible_trips = compatible_trips.filter(accepts_fragile=True)
            
            # Calculer les scores et créer les matches
            matches = []
            for trip in compatible_trips[:limit]:
                score = AutomaticMatchingService.calculate_compatibility_score(
                    shipment, trip, rules
                )
                
                if score >= rules.min_compatibility_score:
                    # Calculer le prix proposé
                    proposed_price = AutomaticMatchingService.calculate_proposed_price(
                        shipment, trip
                    )
                    
                    # Créer ou mettre à jour le match
                    match, created = Match.objects.get_or_create(
                        shipment=shipment,
                        trip=trip,
                        defaults={
                            'compatibility_score': score,
                            'proposed_price': proposed_price,
                            'expires_at': timezone.now() + timezone.timedelta(hours=24),
                            'algorithm_version': '2.0',
                            'matching_factors': AutomaticMatchingService.get_matching_factors(
                                shipment, trip, score
                            )
                        }
                    )
                    
                    if not created:
                        # Mettre à jour le match existant
                        match.compatibility_score = score
                        match.proposed_price = proposed_price
                        match.expires_at = timezone.now() + timezone.timedelta(hours=24)
                        match.matching_factors = AutomaticMatchingService.get_matching_factors(
                            shipment, trip, score
                        )
                        match.save()
                    
                    matches.append(match)
            
            # Trier par score de compatibilité
            matches.sort(key=lambda x: x.compatibility_score, reverse=True)
            
            return matches
            
        except Exception as e:
            logger.error(f"Erreur lors du matching automatique pour l'envoi {shipment.id}: {str(e)}")
            return []
    
    @staticmethod
    def find_matches_for_trip(trip, limit=10):
        """Trouve les meilleurs matches pour un trajet."""
        try:
            # Récupérer les règles de matching actives
            rules = MatchingRule.objects.filter(is_active=True).first()
            if not rules:
                rules = MatchingRule.objects.create(
                    name="Règle par défaut",
                    description="Règle de matching par défaut",
                    is_active=True
                )
            
            # Critères de base
            compatible_shipments = Shipment.objects.filter(
                status='pending',
                weight__lte=trip.remaining_weight
            ).exclude(sender=trip.traveler)
            
            # Filtres géographiques
            origin_matches = Q(origin_city__icontains=trip.origin_city)
            destination_matches = Q(destination_city__icontains=trip.destination_city)
            
            # Correspondances partielles
            if len(trip.origin_city) > 3:
                origin_matches |= Q(origin_city__icontains=trip.origin_city[:3])
            if len(trip.destination_city) > 3:
                destination_matches |= Q(destination_city__icontains=trip.destination_city[:3])
            
            compatible_shipments = compatible_shipments.filter(origin_matches & destination_matches)
            
            # Filtres de type de colis
            if trip.accepted_package_types:
                compatible_shipments = compatible_shipments.filter(
                    package_type__in=trip.accepted_package_types
                )
            
            # Filtre de fragilité
            if not trip.accepts_fragile:
                compatible_shipments = compatible_shipments.filter(is_fragile=False)
            
            # Calculer les scores et créer les matches
            matches = []
            for shipment in compatible_shipments[:limit]:
                score = AutomaticMatchingService.calculate_compatibility_score(
                    shipment, trip, rules
                )
                
                if score >= rules.min_compatibility_score:
                    # Calculer le prix proposé
                    proposed_price = AutomaticMatchingService.calculate_proposed_price(
                        shipment, trip
                    )
                    
                    # Créer ou mettre à jour le match
                    match, created = Match.objects.get_or_create(
                        shipment=shipment,
                        trip=trip,
                        defaults={
                            'compatibility_score': score,
                            'proposed_price': proposed_price,
                            'expires_at': timezone.now() + timezone.timedelta(hours=24),
                            'algorithm_version': '2.0',
                            'matching_factors': AutomaticMatchingService.get_matching_factors(
                                shipment, trip, score
                            )
                        }
                    )
                    
                    if not created:
                        # Mettre à jour le match existant
                        match.compatibility_score = score
                        match.proposed_price = proposed_price
                        match.expires_at = timezone.now() + timezone.timedelta(hours=24)
                        match.matching_factors = AutomaticMatchingService.get_matching_factors(
                            shipment, trip, score
                        )
                        match.save()
                    
                    matches.append(match)
            
            # Trier par score de compatibilité
            matches.sort(key=lambda x: x.compatibility_score, reverse=True)
            
            return matches
            
        except Exception as e:
            logger.error(f"Erreur lors du matching automatique pour le trajet {trip.id}: {str(e)}")
            return []
    
    @staticmethod
    def calculate_compatibility_score(shipment, trip, rules):
        """Calcule le score de compatibilité selon les règles configurées."""
        score = 0.0
        
        # 1. Compatibilité géographique (35%)
        geographic_score = 0.0
        if shipment.origin_city.lower() in trip.origin_city.lower() or trip.origin_city.lower() in shipment.origin_city.lower():
            geographic_score += 0.5
        elif shipment.origin_city.lower()[:3] == trip.origin_city.lower()[:3]:
            geographic_score += 0.3
        
        if shipment.destination_city.lower() in trip.destination_city.lower() or trip.destination_city.lower() in shipment.destination_city.lower():
            geographic_score += 0.5
        elif shipment.destination_city.lower()[:3] == trip.destination_city.lower()[:3]:
            geographic_score += 0.3
        
        score += geographic_score * float(rules.geographic_weight) / 100
        
        # 2. Compatibilité de poids (20%)
        if trip.remaining_weight > 0:
            weight_ratio = float(shipment.weight / trip.remaining_weight)
            if weight_ratio <= 1.0:
                weight_score = 1 - weight_ratio
                score += weight_score * float(rules.weight_weight) / 100
        
        # 3. Compatibilité de type de colis (15%)
        if shipment.package_type in trip.accepted_package_types:
            score += float(rules.package_type_weight) / 100
        
        # 4. Compatibilité de fragilité (10%)
        if shipment.is_fragile and trip.accepts_fragile:
            score += float(rules.fragility_weight) / 100
        elif not shipment.is_fragile:
            score += float(rules.fragility_weight) / 100
        
        # 5. Compatibilité temporelle (15%)
        current_date = timezone.now().date()
        departure_date = trip.departure_date.date()
        if departure_date >= current_date:
            days_diff = (departure_date - current_date).days
            if days_diff <= 7:
                date_score = 1.0
            elif days_diff <= 14:
                date_score = 0.7
            elif days_diff <= 30:
                date_score = 0.4
            else:
                date_score = 0.1
            
            score += date_score * float(rules.date_weight) / 100
        
        # 6. Réputation du voyageur (5%)
        user_rating = getattr(trip.traveler, 'rating', 0)
        reputation_score = float(user_rating) / 5.0
        score += reputation_score * float(rules.reputation_weight) / 100
        
        return min(score * 100, 100.0)  # Normaliser entre 0 et 100
    
    @staticmethod
    def calculate_proposed_price(shipment, trip):
        """Calcule le prix proposé"""
        # Prix de base par kg
        base_price_per_kg = trip.min_price_per_kg or Decimal('1000.00')
        
        # Prix de base
        base_price = shipment.weight * base_price_per_kg
        
        # Majoration selon l'urgence
        urgency_multiplier = {
            'low': 1.0,
            'medium': 1.1,
            'high': 1.2,
            'urgent': 1.5
        }
        
        urgency_multiplier_value = urgency_multiplier.get(shipment.urgency, 1.0)
        
        # Majoration pour colis fragile
        fragility_multiplier = 1.2 if shipment.is_fragile else 1.0
        
        # Calcul du prix final
        final_price = base_price * Decimal(str(urgency_multiplier_value)) * Decimal(str(fragility_multiplier))
        
        return final_price
    
    @staticmethod
    def get_matching_factors(shipment, trip, score):
        """Retourne les facteurs de matching détaillés."""
        return {
            'geographic_match': {
                'origin_match': shipment.origin_city.lower() in trip.origin_city.lower(),
                'destination_match': shipment.destination_city.lower() in trip.destination_city.lower(),
                'score': 35.0
            },
            'weight_compatibility': {
                'weight_ratio': float(shipment.weight / trip.remaining_weight),
                'score': 20.0
            },
            'package_type_match': {
                'matched': shipment.package_type in trip.accepted_package_types,
                'score': 15.0
            },
            'fragility_match': {
                'matched': not shipment.is_fragile or trip.accepts_fragile,
                'score': 10.0
            },
            'date_compatibility': {
                'days_until_departure': (trip.departure_date.date() - timezone.now().date()).days,
                'score': 15.0
            },
            'traveler_reputation': {
                'rating': float(getattr(trip.traveler, 'rating', 0)),
                'score': 5.0
            }
        }


class MatchingNotificationService:
    """Service pour les notifications de matching."""
    
    @staticmethod
    def send_match_notification(match):
        """Envoie une notification pour un nouveau match."""
        try:
            # Marquer la notification comme envoyée
            match.notification_sent = True
            match.notification_sent_at = timezone.now()
            match.save()
            
            # Ici, vous pouvez intégrer avec votre système de notifications existant
            # Par exemple, envoyer un email ou une notification push
            
            logger.info(f"Notification de match envoyée pour le match {match.id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification pour le match {match.id}: {str(e)}")
            return False
    
    @staticmethod
    def send_otp_notification(match):
        """Envoie une notification avec l'OTP de livraison."""
        try:
            # Ici, vous pouvez intégrer avec votre système de notifications existant
            # pour envoyer l'OTP par SMS ou email au destinataire
            
            logger.info(f"OTP de livraison envoyé pour le match {match.id}: {match.delivery_otp}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'OTP pour le match {match.id}: {str(e)}")
            return False


class OTPDeliveryService:
    """Service pour la gestion des OTP de livraison."""
    
    @staticmethod
    def generate_and_send_otp(match):
        """Génère et envoie l'OTP de livraison."""
        try:
            # Générer l'OTP
            otp_code = match.generate_delivery_otp()
            
            # Envoyer la notification
            MatchingNotificationService.send_otp_notification(match)
            
            return otp_code
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de l'OTP pour le match {match.id}: {str(e)}")
            return None
    
    @staticmethod
    def verify_delivery_otp(match, otp_code):
        """Vérifie l'OTP de livraison et confirme la livraison."""
        try:
            if match.verify_delivery_otp(otp_code):
                # Libérer le paiement au voyageur
                OTPDeliveryService.release_payment_to_traveler(match)
                
                # Mettre à jour le statut de l'envoi
                match.shipment.status = 'delivered'
                match.shipment.delivery_date = timezone.now()
                match.shipment.save()
                
                logger.info(f"Livraison confirmée pour le match {match.id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'OTP pour le match {match.id}: {str(e)}")
            return False
    
    @staticmethod
    def release_payment_to_traveler(match):
        """Libère le paiement au voyageur après confirmation de livraison."""
        try:
            # Ici, vous pouvez intégrer avec votre système de paiements existant
            # pour libérer les gains du voyageur
            
            logger.info(f"Paiement libéré au voyageur pour le match {match.id}: {match.traveler_earnings}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la libération du paiement pour le match {match.id}: {str(e)}")
            return False


class MatchingAnalyticsService:
    """Service pour les analytics de matching."""
    
    @staticmethod
    def get_matching_statistics(user=None, date_from=None, date_to=None):
        """Récupère les statistiques de matching."""
        try:
            matches = Match.objects.all()
            
            if user:
                matches = matches.filter(
                    Q(shipment__sender=user) | Q(trip__traveler=user)
                )
            
            if date_from:
                matches = matches.filter(created_at__gte=date_from)
            
            if date_to:
                matches = matches.filter(created_at__lte=date_to)
            
            stats = {
                'total_matches': matches.count(),
                'accepted_matches': matches.filter(status='accepted').count(),
                'rejected_matches': matches.filter(status='rejected').count(),
                'pending_matches': matches.filter(status='pending').count(),
                'expired_matches': matches.filter(status='expired').count(),
                'average_compatibility_score': matches.aggregate(
                    avg_score=models.Avg('compatibility_score')
                )['avg_score'] or 0,
                'success_rate': (matches.filter(status='accepted').count() / 
                               max(matches.count(), 1)) * 100,
                'total_earnings': matches.filter(status='accepted').aggregate(
                    total=models.Sum('traveler_earnings')
                )['total'] or 0,
                'total_commission': matches.filter(status='accepted').aggregate(
                    total=models.Sum('commission_amount')
                )['total'] or 0
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques de matching: {str(e)}")
            return {
                'total_matches': 0,
                'accepted_matches': 0,
                'rejected_matches': 0,
                'pending_matches': 0,
                'expired_matches': 0,
                'average_compatibility_score': 0,
                'success_rate': 0,
                'total_earnings': 0,
                'total_commission': 0
            }
