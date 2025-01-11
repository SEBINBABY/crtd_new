from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from functools import wraps
from admin_dashboard.models import User
from .models import *

def user_only(view_func):
    @wraps(view_func)
    @login_required()
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

def get_next_quiz(user_id):
    """Returns the next quiz the user is supposed to attempt"""
    results = Result.objects.filter(user_id=user_id)
    available_quizzes = Quiz.objects.exclude(id__in=results.values_list('quiz_id', flat=True))
    if not available_quizzes.exists():
        None

    return available_quizzes.first()

def is_test_started(request):
    if Result.objects.filter(user=request.user,end_time__isnull=True).exists():
        return True
    
