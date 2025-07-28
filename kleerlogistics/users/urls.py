"""
URLs for users app - Authentication and user management
"""

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from . import views

app_name = 'users'

urlpatterns = [
    # JWT Authentication
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # User Registration and Management
    path('register/', views.UserRegistrationView.as_view(), name='user_register'),
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('profile/update/', views.UserProfileUpdateView.as_view(), name='user_profile_update'),
    
    # Phone Verification
    path('verify-phone/', views.PhoneVerificationView.as_view(), name='phone_verification'),
    path('verify-phone/send-otp/', views.SendOTPView.as_view(), name='send_otp'),
    path('verify-phone/verify-otp/', views.VerifyOTPView.as_view(), name='verify_otp'),
    
    # Password Management
    path('password/change/', views.ChangePasswordView.as_view(), name='change_password'),
    path('password/reset/', views.ResetPasswordView.as_view(), name='reset_password'),
    path('password/reset/confirm/', views.ResetPasswordConfirmView.as_view(), name='reset_password_confirm'),
    
    # Document Management
    path('documents/', views.UserDocumentListView.as_view(), name='user_documents'),
    path('documents/upload/', views.UserDocumentUploadView.as_view(), name='upload_document'),
    path('documents/<int:pk>/', views.UserDocumentDetailView.as_view(), name='document_detail'),
    
    # User Search (for matching)
    path('search/', views.UserSearchView.as_view(), name='user_search'),
    
    # Admin endpoints (if needed)
    path('admin/users/', views.AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/users/<int:pk>/', views.AdminUserDetailView.as_view(), name='admin_user_detail'),
] 