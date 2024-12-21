from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path("", views.verify_passkey, name="verify_passkey"),
    path("register/", views.register, name="register"),
    path("register_verified/", views.register_verified, name="register_verified"),
    path("otp_page/", views.otp_page, name="otp_page"),
    path("user_login/", views.user_login, name="user_login"),
    path("user_logout/", views.user_logout, name="user_logout"),
    path("send_email_verification_otp/", views.send_email_verification_otp, name="send_email_verification_otp"),
    path("verify_email_otp/", views.verify_email_otp, name="verify_email_otp"),
    
    # Password reset using email
    path('reset_password/', views.ResetPasswordView.as_view(), name='reset_password'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('password_reset_complete/', views.CustomPasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html'), name='password_reset_complete'),
]
