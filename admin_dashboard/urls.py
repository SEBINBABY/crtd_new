from django.urls import path
from .views import admin_hr_login, question_section, user_list, passkey, add_passkey, update_passkey, delete_user
from .views import *

app_name = "admin_dashboard"

urlpatterns = [
    path('admin_hr_login/', admin_hr_login, name='admin_hr_login'),
    path('admin_hr_logout/', admin_hr_logout, name='admin_hr_logout'), 
    path('dashboard_home/', dashboard_home, name='dashboard_home'),
    path('question_section/', question_section, name='question_section'),
    path('question_list/<int:quiz_id>', question_list, name='question_list'),
    path('user_list/', user_list, name="user_list"),
    path('passkey/', passkey, name="passkey"),
    path('add_passkey/', add_passkey, name="add_passkey"),
    path('update_passkey/<int:passkey_id>/', update_passkey, name="update_passkey"),
    path('delete_passkey/<int:passkey_id>/', delete_passkey, name="delete_passkey"),
    path('get_user_results/<int:user_id>/', get_user_results, name="get_user_results"),
    path('edit_question/', edit_question, name="edit_question"),
    path('add_question/', add_question, name="add_question"),
    path('delete_question/', delete_question, name="delete_question"),
    path('amount_section/', amount_section, name="amount_section"),
    path('add_quiz/', add_quiz, name="add_quiz"),
    path('edit_quiz/', edit_quiz, name="edit_quiz"),
    path('delete_quiz/', delete_quiz, name="delete_quiz"),
    path('reorder_quizzes/', reorder_quizzes, name="reorder_quizzes"),
     path('delete_user/',delete_user, name='delete_user'),
]


