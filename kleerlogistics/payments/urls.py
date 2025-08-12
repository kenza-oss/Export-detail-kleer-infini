"""
URLs pour la gestion des paiements algériens
Support pour CIB, Eddahabia et paiement en espèces au bureau
"""

from django.urls import path
from .views import (
    PaymentMethodsView, CardPaymentView, CashPaymentView,
    CashPaymentConfirmationView, PaymentFeesView,
    PaymentStatisticsView, TransactionDetailView
)

app_name = 'payments'

urlpatterns = [
    # Méthodes de paiement
    path('methods/', PaymentMethodsView.as_view(), name='payment_methods'),
    
    # Paiements par carte bancaire algérienne
    path('card/', CardPaymentView.as_view(), name='card_payment'),
    
    # Paiements en espèces
    path('cash/', CashPaymentView.as_view(), name='cash_payment'),
    path('cash/<str:transaction_id>/confirm/', CashPaymentConfirmationView.as_view(), name='cash_payment_confirm'),
    
    # Calcul des frais
    path('fees/', PaymentFeesView.as_view(), name='payment_fees'),
    
    # Statistiques (admin)
    path('statistics/', PaymentStatisticsView.as_view(), name='payment_statistics'),
    
    # Détails des transactions
    path('transactions/<str:transaction_id>/', TransactionDetailView.as_view(), name='transaction_detail'),
] 