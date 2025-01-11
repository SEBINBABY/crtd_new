from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from functools import wraps
from admin_dashboard.models import User
from django.db.models import Max
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
    

def generate_unique_tcn():
    # Get the maximum TCN number from the database
    max_tcn = User.objects.aggregate(Max('tcn_number'))['tcn_number__max']
    
    if max_tcn:
        # Increment the maximum TCN number by 1
        next_tcn = int(max_tcn) + 1
    else:
        # Start with 1 if no TCN exists
        next_tcn = 1
    
    # Format the TCN as a 5-digit string with leading zeros
    return f"{next_tcn:05}"