from django.urls import path
from . import views

app_name = "quiz"

urlpatterns = [
    path("list_quizzes/", views.list_quizzes, name="list_quizzes"),
    path("start_test/", views.start_test, name="start_test"),
    path('quiz/<int:quiz_id>/question/<int:question_id>/', views.start_question, name='start_question'),
    path('quiz/<int:quiz_id>/save_answer/<int:question_id>/', views.save_answer, name='save_answer'),
    path("quiz_summary/<int:quiz_id>", views.quiz_summary, name="quiz_summary"),  
    path("finish_test/", views.finish_test, name="finish_test"),
    path("get_remaining_time/", views.get_remaining_time, name="get_remaining_time"),

]