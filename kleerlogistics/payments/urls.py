"""
URLs for payments app - Payment and wallet management
"""

from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Wallet Management
    path('wallet/', views.WalletView.as_view(), name='wallet'),
    
    # Transaction Management
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    
    # Payment Operations
    path('deposit/', views.DepositView.as_view(), name='deposit'),
    path('withdraw/', views.WithdrawView.as_view(), name='withdraw'),
    path('transfer/', views.TransferView.as_view(), name='transfer'),
    
    # Chargily Pay Integration
    path('chargily-pay/create/', views.ChargilyPayView.as_view(), name='chargily_pay_create'),
    path('chargily-pay/callback/', views.ChargilyPayCallbackView.as_view(), name='chargily_pay_callback'),
    
    # Shipment Payment Processing
    path('shipments/<int:shipment_id>/process-payment/', views.ProcessShipmentPaymentView.as_view(), name='process_shipment_payment'),
    
    # Commission Management
    path('commissions/', views.CommissionListView.as_view(), name='commission_list'),
    
    # Refund Management
    path('refunds/<int:transaction_id>/', views.RefundView.as_view(), name='refund'),
    
    # Payment Analytics
    path('analytics/', views.PaymentAnalyticsView.as_view(), name='payment_analytics'),
    
    # Admin endpoints
    path('admin/transactions/', views.AdminTransactionListView.as_view(), name='admin_transaction_list'),
    path('admin/wallets/', views.AdminWalletListView.as_view(), name='admin_wallet_list'),
] 