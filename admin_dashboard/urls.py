from django.urls import path
from .views import filtered_users, admin_hr_login,dashboard, filtered_users

app_name = "admin_dashboard"

urlpatterns = [
    path('users/<str:status>/', filtered_users, name='filtered_users'),
    path('admin_hr_login/', admin_hr_login, name='admin_hr_login'),
    path('dashboard/', dashboard, name='dashboard'),
    # path('filtered_users/<str:status>', filtered_users, name='filtered_users'),

]
