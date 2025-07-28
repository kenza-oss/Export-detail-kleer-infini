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
] 