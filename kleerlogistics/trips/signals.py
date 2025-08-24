"""
Signaux pour le module trips - Gestion des événements automatiques
"""

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from .models import Trip, TripDocument


@receiver(post_save, sender=Trip)
def trip_post_save(sender, instance, created, **kwargs):
    """Gérer les événements après sauvegarde d'un trajet."""
    if created:
        # Nouveau trajet créé
        send_trip_created_notification(instance)
    else:
        # Trajet modifié
        send_trip_updated_notification(instance)
        
        # Vérifier si le trajet doit être expiré
        check_trip_expiration(instance)


@receiver(pre_save, sender=Trip)
def trip_pre_save(sender, instance, **kwargs):
    """Gérer les événements avant sauvegarde d'un trajet."""
    if instance.pk:  # Modification d'un trajet existant
        try:
            old_instance = Trip.objects.get(pk=instance.pk)
            
            # Si le statut a changé
            if old_instance.status != instance.status:
                handle_trip_status_change(old_instance, instance)
                
            # Si la vérification a changé
            if not old_instance.is_verified and instance.is_verified:
                send_trip_verified_notification(instance)
                
        except Trip.DoesNotExist:
            pass


@receiver(post_save, sender=TripDocument)
def trip_document_post_save(sender, instance, created, **kwargs):
    """Gérer les événements après sauvegarde d'un document."""
    if created:
        send_document_uploaded_notification(instance)
    else:
        if instance.is_verified:
            send_document_verified_notification(instance)


@receiver(post_delete, sender=Trip)
def trip_post_delete(sender, instance, **kwargs):
    """Gérer les événements après suppression d'un trajet."""
    send_trip_deleted_notification(instance)


def send_trip_created_notification(trip):
    """Envoyer une notification de création de trajet."""
    try:
        subject = f"Nouveau trajet créé: {trip.origin_city} → {trip.destination_city}"
        
        context = {
            'trip': trip,
            'traveler': trip.traveler,
            'route': f"{trip.origin_city} → {trip.destination_city}",
            'departure_date': trip.departure_date.strftime('%d/%m/%Y %H:%M'),
            'max_weight': trip.max_weight,
            'max_packages': trip.max_packages,
            'min_price': trip.min_price_per_kg
        }
        
        # Email au voyageur
        if trip.traveler.email:
            html_message = render_to_string('trips/emails/trip_created.html', context)
            text_message = render_to_string('trips/emails/trip_created.txt', context)
            
            send_mail(
                subject=subject,
                message=text_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[trip.traveler.email],
                fail_silently=True
            )
        
        # Email aux administrateurs
        admin_emails = get_admin_emails()
        if admin_emails:
            admin_context = context.copy()
            admin_context['is_admin'] = True
            
            html_message = render_to_string('trips/emails/trip_created_admin.html', admin_context)
            text_message = render_to_string('trips/emails/trip_created_admin.txt', admin_context)
            
            send_mail(
                subject=f"[ADMIN] {subject}",
                message=text_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=True
            )
            
    except Exception as e:
        # Logger l'erreur mais ne pas faire échouer le processus
        print(f"Erreur lors de l'envoi de la notification de création: {e}")


def send_trip_updated_notification(trip):
    """Envoyer une notification de modification de trajet."""
    try:
        subject = f"Trajet modifié: {trip.origin_city} → {trip.destination_city}"
        
        context = {
            'trip': trip,
            'traveler': trip.traveler,
            'route': f"{trip.origin_city} → {trip.destination_city}",
            'departure_date': trip.departure_date.strftime('%d/%m/%Y %H:%M'),
            'status': trip.get_status_display()
        }
        
        if trip.traveler.email:
            html_message = render_to_string('trips/emails/trip_updated.html', context)
            text_message = render_to_string('trips/emails/trip_updated.txt', context)
            
            send_mail(
                subject=subject,
                message=text_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[trip.traveler.email],
                fail_silently=True
            )
            
    except Exception as e:
        print(f"Erreur lors de l'envoi de la notification de modification: {e}")


def send_trip_verified_notification(trip):
    """Envoyer une notification de vérification de trajet."""
    try:
        subject = f"Trajet vérifié: {trip.origin_city} → {trip.destination_city}"
        
        context = {
            'trip': trip,
            'traveler': trip.traveler,
            'route': f"{trip.origin_city} → {trip.destination_city}",
            'departure_date': trip.departure_date.strftime('%d/%m/%Y %H:%M')
        }
        
        if trip.traveler.email:
            html_message = render_to_string('trips/emails/trip_verified.html', context)
            text_message = render_to_string('trips/emails/trip_verified.txt', context)
            
            send_mail(
                subject=subject,
                message=text_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[trip.traveler.email],
                fail_silently=True
            )
            
    except Exception as e:
        print(f"Erreur lors de l'envoi de la notification de vérification: {e}")


def send_trip_deleted_notification(trip):
    """Envoyer une notification de suppression de trajet."""
    try:
        subject = f"Trajet supprimé: {trip.origin_city} → {trip.destination_city}"
        
        context = {
            'trip': trip,
            'traveler': trip.traveler,
            'route': f"{trip.origin_city} → {trip.destination_city}"
        }
        
        # Email aux administrateurs
        admin_emails = get_admin_emails()
        if admin_emails:
            admin_context = context.copy()
            admin_context['is_admin'] = True
            
            html_message = render_to_string('trips/emails/trip_deleted_admin.html', admin_context)
            text_message = render_to_string('trips/emails/trip_deleted_admin.txt', admin_context)
            
            send_mail(
                subject=f"[ADMIN] {subject}",
                message=text_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=True
            )
            
    except Exception as e:
        print(f"Erreur lors de l'envoi de la notification de suppression: {e}")


def send_document_uploaded_notification(document):
    """Envoyer une notification d'upload de document."""
    try:
        subject = f"Document uploadé pour le trajet #{document.trip.id}"
        
        context = {
            'document': document,
            'trip': document.trip,
            'traveler': document.trip.traveler,
            'document_type': document.get_document_type_display()
        }
        
        # Email aux administrateurs
        admin_emails = get_admin_emails()
        if admin_emails:
            html_message = render_to_string('trips/emails/document_uploaded_admin.html', context)
            text_message = render_to_string('trips/emails/document_uploaded_admin.txt', context)
            
            send_mail(
                subject=f"[ADMIN] {subject}",
                message=text_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=True
            )
            
    except Exception as e:
        print(f"Erreur lors de l'envoi de la notification d'upload: {e}")


def send_document_verified_notification(document):
    """Envoyer une notification de vérification de document."""
    try:
        subject = f"Document vérifié pour le trajet #{document.trip.id}"
        
        context = {
            'document': document,
            'trip': document.trip,
            'traveler': document.trip.traveler,
            'document_type': document.get_document_type_display()
        }
        
        if document.trip.traveler.email:
            html_message = render_to_string('trips/emails/document_verified.html', context)
            text_message = render_to_string('trips/emails/document_verified.txt', context)
            
            send_mail(
                subject=subject,
                message=text_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[document.trip.traveler.email],
                fail_silently=True
            )
            
    except Exception as e:
        print(f"Erreur lors de l'envoi de la notification de vérification: {e}")


def handle_trip_status_change(old_instance, new_instance):
    """Gérer le changement de statut d'un trajet."""
    try:
        if new_instance.status == 'active' and old_instance.status == 'draft':
            # Trajet activé
            send_trip_activated_notification(new_instance)
        elif new_instance.status == 'completed' and old_instance.status == 'in_progress':
            # Trajet terminé
            send_trip_completed_notification(new_instance)
        elif new_instance.status == 'cancelled':
            # Trajet annulé
            send_trip_cancelled_notification(new_instance)
            
    except Exception as e:
        print(f"Erreur lors de la gestion du changement de statut: {e}")


def send_trip_activated_notification(trip):
    """Envoyer une notification d'activation de trajet."""
    try:
        subject = f"Trajet activé: {trip.origin_city} → {trip.destination_city}"
        
        context = {
            'trip': trip,
            'traveler': trip.traveler,
            'route': f"{trip.origin_city} → {trip.destination_city}",
            'departure_date': trip.departure_date.strftime('%d/%m/%Y %H:%M')
        }
        
        if trip.traveler.email:
            html_message = render_to_string('trips/emails/trip_activated.html', context)
            text_message = render_to_string('trips/emails/trip_activated.txt', context)
            
            send_mail(
                subject=subject,
                message=text_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[trip.traveler.email],
                fail_silently=True
            )
            
    except Exception as e:
        print(f"Erreur lors de l'envoi de la notification d'activation: {e}")


def send_trip_completed_notification(trip):
    """Envoyer une notification de completion de trajet."""
    try:
        subject = f"Trajet terminé: {trip.origin_city} → {trip.destination_city}"
        
        context = {
            'trip': trip,
            'traveler': trip.traveler,
            'route': f"{trip.origin_city} → {trip.destination_city}",
            'earnings': trip.estimated_earnings
        }
        
        if trip.traveler.email:
            html_message = render_to_string('trips/emails/trip_completed.html', context)
            text_message = render_to_string('trips/emails/trip_completed.txt', context)
            
            send_mail(
                subject=subject,
                message=text_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[trip.traveler.email],
                fail_silently=True
            )
            
    except Exception as e:
        print(f"Erreur lors de l'envoi de la notification de completion: {e}")


def send_trip_cancelled_notification(trip):
    """Envoyer une notification d'annulation de trajet."""
    try:
        subject = f"Trajet annulé: {trip.origin_city} → {trip.destination_city}"
        
        context = {
            'trip': trip,
            'traveler': trip.traveler,
            'route': f"{trip.origin_city} → {trip.destination_city}"
        }
        
        if trip.traveler.email:
            html_message = render_to_string('trips/emails/trip_cancelled.html', context)
            text_message = render_to_string('trips/emails/trip_cancelled.txt', context)
            
            send_mail(
                subject=subject,
                message=text_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[trip.traveler.email],
                fail_silently=True
            )
            
    except Exception as e:
        print(f"Erreur lors de l'envoi de la notification d'annulation: {e}")


def check_trip_expiration(trip):
    """Vérifier si un trajet doit être expiré."""
    try:
        if (trip.status == 'active' and 
            trip.departure_date < timezone.now() and 
            not trip.is_active):
            
            trip.status = 'expired'
            trip.save(update_fields=['status'])
            
            # Envoyer notification d'expiration
            send_trip_expired_notification(trip)
            
    except Exception as e:
        print(f"Erreur lors de la vérification d'expiration: {e}")


def send_trip_expired_notification(trip):
    """Envoyer une notification d'expiration de trajet."""
    try:
        subject = f"Trajet expiré: {trip.origin_city} → {trip.destination_city}"
        
        context = {
            'trip': trip,
            'traveler': trip.traveler,
            'route': f"{trip.origin_city} → {trip.destination_city}",
            'departure_date': trip.departure_date.strftime('%d/%m/%Y %H:%M')
        }
        
        if trip.traveler.email:
            html_message = render_to_string('trips/emails/trip_expired.html', context)
            text_message = render_to_string('trips/emails/trip_expired.txt', context)
            
            send_mail(
                subject=subject,
                message=text_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[trip.traveler.email],
                fail_silently=True
            )
            
    except Exception as e:
        print(f"Erreur lors de l'envoi de la notification d'expiration: {e}")


def get_admin_emails():
    """Récupérer la liste des emails administrateurs."""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        admin_emails = list(User.objects.filter(
            is_staff=True, 
            is_active=True
        ).values_list('email', flat=True))
        
        return admin_emails
    except Exception:
        return []


# Fonction utilitaire pour expirer automatiquement les trajets
def expire_expired_trips():
    """Expirer automatiquement tous les trajets en retard."""
    try:
        expired_trips = Trip.objects.filter(
            status='active',
            departure_date__lt=timezone.now()
        )
        
        count = expired_trips.update(status='expired')
        
        if count > 0:
            print(f"{count} trajets ont été expirés automatiquement")
            
            # Envoyer notifications d'expiration
            for trip in expired_trips:
                send_trip_expired_notification(trip)
                
    except Exception as e:
        print(f"Erreur lors de l'expiration automatique des trajets: {e}")


# Fonction utilitaire pour nettoyer les anciens trajets
def cleanup_old_trips():
    """Nettoyer les anciens trajets (plus de 6 mois)."""
    try:
        cutoff_date = timezone.now() - timezone.timedelta(days=180)
        
        old_trips = Trip.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['completed', 'cancelled', 'expired']
        )
        
        count = old_trips.count()
        old_trips.delete()
        
        if count > 0:
            print(f"{count} anciens trajets ont été supprimés")
            
    except Exception as e:
        print(f"Erreur lors du nettoyage des anciens trajets: {e}")
