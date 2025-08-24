"""
URLs pour la gestion des paiements algériens
Support pour CIB, Eddahabia et paiement en espèces au bureau
"""

from django.urls import path
from .views import (
    PaymentMethodsView, CardPaymentView, CashPaymentView,
    CashPaymentConfirmationView, PaymentFeesView,
    PaymentStatisticsView, TransactionDetailView,
    WalletView, WalletBalanceView, WalletTransactionsView,
    WalletDepositView, WalletWithdrawView, WalletTransferView,
    ChargilyPaymentView, ChargilyPaymentStatusView, ChargilyWebhookView,
    CommissionView, CommissionCalculateView, CommissionApplyView,
    BankTransferRequestView, BankTransferConfirmView, BankTransferHistoryView,
    CashPaymentOfficesView, TransactionListView, TransactionCancelView,
    TransactionRefundView, FeesCalculateView
)

app_name = 'payments'

urlpatterns = [
    # Méthodes de paiement
    path('methods/', PaymentMethodsView.as_view(), name='payment_methods'),
    path('methods/<str:method_name>/', PaymentMethodsView.as_view(), name='payment_method_detail'),
    
    # Paiements par carte bancaire algérienne
    path('card/', CardPaymentView.as_view(), name='card_payment'),
    
    # Paiements en espèces
    path('cash/', CashPaymentView.as_view(), name='cash_payment'),
    path('cash/<str:transaction_id>/confirm/', CashPaymentConfirmationView.as_view(), name='cash_payment_confirm'),
    
    # Calcul des frais
    path('fees/', PaymentFeesView.as_view(), name='payment_fees'),
    path('fees/calculate/', FeesCalculateView.as_view(), name='fees_calculate'),
    
    # Statistiques
    path('statistics/', PaymentStatisticsView.as_view(), name='payment_statistics'),
    
    # Gestion des portefeuilles virtuels (fonctionnalités supplémentaires)
    path('wallet/', WalletView.as_view(), name='wallet'),
    path('wallet/balance/', WalletBalanceView.as_view(), name='wallet_balance'),
    path('wallet/transactions/', WalletTransactionsView.as_view(), name='wallet_transactions'),
    path('wallet/deposit/', WalletDepositView.as_view(), name='wallet_deposit'),
    path('wallet/withdraw/', WalletWithdrawView.as_view(), name='wallet_withdraw'),
    path('wallet/transfer/', WalletTransferView.as_view(), name='wallet_transfer'),
    
    # Intégration Chargily Pay (fonctionnalités supplémentaires)
    path('chargily-payment/', ChargilyPaymentView.as_view(), name='chargily_payment'),
    path('chargily-payment/status/<str:transaction_id>/', ChargilyPaymentStatusView.as_view(), name='chargily_payment_status'),
    path('webhooks/chargily/', ChargilyWebhookView.as_view(), name='chargily_webhook'),
    
    # Gestion des commissions (fonctionnalités supplémentaires)
    path('commissions/', CommissionView.as_view(), name='commissions'),
    path('commissions/calculate/', CommissionCalculateView.as_view(), name='commissions_calculate'),
    path('commissions/apply/', CommissionApplyView.as_view(), name='commissions_apply'),
    
    # Gestion des virements bancaires (fonctionnalités supplémentaires)
    path('bank-transfer/request/', BankTransferRequestView.as_view(), name='bank_transfer_request'),
    path('bank-transfer/confirm/', BankTransferConfirmView.as_view(), name='bank_transfer_confirm'),
    path('bank-transfer/history/', BankTransferHistoryView.as_view(), name='bank_transfer_history'),
    
    # Bureaux de paiement (fonctionnalités supplémentaires)
    path('cash-payment/offices/', CashPaymentOfficesView.as_view(), name='cash_payment_offices'),
    
    # Gestion des transactions (fonctionnalités supplémentaires)
    path('transactions/', TransactionListView.as_view(), name='transaction_list'),
    path('transactions/<str:transaction_id>/', TransactionDetailView.as_view(), name='transaction_detail'),
    path('transactions/<str:transaction_id>/cancel/', TransactionCancelView.as_view(), name='transaction_cancel'),
    path('transactions/<str:transaction_id>/refund/', TransactionRefundView.as_view(), name='transaction_refund'),
] 