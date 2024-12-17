from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from functools import wraps
from admin_dashboard.models import User
from .models import *

PAYMENT_KEYWORD = "payment"

def user_only(view_func):
    @wraps(view_func)
    @login_required(login_url="/user_login")
    def _wrapped_view(request, *args, **kwargs):
        if request.user.role == User.USER:
            return view_func(request, *args, **kwargs)
        # Redirect to login page or show an error
        return redirect('users:user_login')
    return _wrapped_view


# HELPER FUNCTIONS
def calculate_score(quiz,result):
    # Calculate score
    total_questions = quiz.quiz_questions.count()
    correct_answers = 0

    for question in quiz.quiz_questions.all():
        selected_answer_id = result.user_answers.get(str(question.id))
        if selected_answer_id:
            selected_answer = Answer.objects.get(id=selected_answer_id)
            if selected_answer.is_correct:
                correct_answers += 1

    return(correct_answers / total_questions) * 100


def requires_payment(quiz):
    return PAYMENT_KEYWORD.lower() in quiz.name.lower()

def get_next_quiz(results):
# Start a new quiz
    available_quizzes = Quiz.objects.exclude(id__in=results.values_list('quiz_id', flat=True))
    if not available_quizzes.exists():
        None

    return available_quizzes.first()
    