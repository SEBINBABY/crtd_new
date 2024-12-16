from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path("", views.verify_passkey, name="verify_passkey"),
    path("register/", views.register, name="register"),
    path("register_verified/", views.register_verified, name="register_verified"),
    path("otp_page/", views.otp_page, name="otp_page"),
    path("user_login/", views.user_login, name="user_login"),
    path("send_email_verification_otp/", views.send_email_verification_otp, name="send_email_verification_otp"),
    path("verify_email_otp/", views.verify_email_otp, name="verify_email_otp"),
    # path("question/", views.question, name="question"),
]
    # path("exam-instructions/", views.exam_instructions, name="exam_instructions"),
    # path("start-exam/", views.start_exam, name="start_exam"),
    # path("exam-section/<int:section_id>/", views.exam_section, name="exam_section"),
    # path("exam-complete/", views.exam_complete, name="exam_complete"),

    # path('response/', views.response, name='response')
