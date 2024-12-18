from django.urls import path
from .views import filtered_users, admin_hr_login,dashboard, filtered_users, question_section, user_list, passkey
from .views import *

app_name = "admin_dashboard"

urlpatterns = [
    path('users/<str:status>/', filtered_users, name='filtered_users'),
    path('admin_hr_login/', admin_hr_login, name='admin_hr_login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('question_section/', question_section, name='question_section'),
    path('question_list/<int:quiz_id>', question_list, name='question_list'),
    path('user_list/', user_list, name="user_list"),
    path('passkey/', passkey, name="passkey"),
]


