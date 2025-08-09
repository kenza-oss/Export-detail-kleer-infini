"""
URLs for users app - Authentication and user management
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication JWT
    path('auth/login/', views.UserLoginView.as_view(), name='user_login'),
    path('auth/register/', views.UserRegistrationView.as_view(), name='user_registration'),
    path('auth/logout/', views.UserLogoutView.as_view(), name='user_logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # OTP Verification
    path('auth/otp/send/', views.SendOTPView.as_view(), name='send_otp'),
    path('auth/otp/verify/', views.VerifyOTPView.as_view(), name='verify_otp'),
    path('auth/phone/status/', views.PhoneVerificationView.as_view(), name='phone_verification_status'),
    
    # Password Management
    path('auth/password/change/', views.ChangePasswordView.as_view(), name='change_password'),
    path('auth/password/reset/', views.ResetPasswordView.as_view(), name='reset_password'),
    path('auth/password/reset/confirm/', views.ResetPasswordConfirmView.as_view(), name='reset_password_confirm'),
    
    # User Profile
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('profile/update/', views.UserProfileUpdateView.as_view(), name='user_profile_update'),
    
    # User Permissions
    path('permissions/', views.UserPermissionsView.as_view(), name='user_permissions'),
    
    # User Status
    path('status/', views.UserStatusView.as_view(), name='user_status'),
    path('verification-status/', views.UserVerificationStatusView.as_view(), name='user_verification_status'),
    path('request-verification/', views.UserRequestVerificationView.as_view(), name='user_request_verification'),

    # User Preferences
    path('preferences/language/', views.UserLanguagePreferenceView.as_view(), name='user_language_preference'),
    path('preferences/commission/', views.UserCommissionPreferenceView.as_view(), name='user_commission_preference'),

    # User Activity Status
    path('activate-sender/', views.UserActivateSenderView.as_view(), name='user_activate_sender'),
    path('activate-traveler/', views.UserActivateTravelerView.as_view(), name='user_activate_traveler'),
    path('deactivate-sender/', views.UserDeactivateSenderView.as_view(), name='user_deactivate_sender'),
    path('deactivate-traveler/', views.UserDeactivateTravelerView.as_view(), name='user_deactivate_traveler'),

    # User Analytics
    path('analytics/', views.UserAnalyticsView.as_view(), name='user_analytics'),
    path('performance/', views.UserPerformanceView.as_view(), name='user_performance'),
    
    # User Stats
    path('stats/', views.UserStatsView.as_view(), name='user_stats'),
    
    # User Documents
    path('documents/', views.UserDocumentListView.as_view(), name='user_documents'),
    path('documents/upload/', views.UserDocumentUploadView.as_view(), name='user_document_upload'),
    path('documents/<int:pk>/', views.UserDocumentDetailView.as_view(), name='user_document_detail'),
    
    # User Search
    path('search/', views.UserSearchView.as_view(), name='user_search'),
    
    # Admin Views
    path('admin/users/', views.AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/users/<int:pk>/', views.AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('admin/users/<int:user_id>/role/', views.RoleUpdateView.as_view(), name='admin_role_update'),
    
    # Wallet (Backward compatibility)
    path('wallet/', views.UserWalletView.as_view(), name='user_wallet'),
    path('wallet/deposit/', views.UserDepositView.as_view(), name='user_wallet_deposit'),
    path('wallet/withdraw/', views.UserWithdrawView.as_view(), name='user_wallet_withdraw'),
    path('wallet/transfer/', views.UserTransferView.as_view(), name='user_wallet_transfer'),
    path('wallet/transactions/', views.UserTransactionListView.as_view(), name='user_wallet_transactions'),
] 