import random
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Quiz, Question, Answer, Result
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now 
from django.contrib import messages
from admin_dashboard.models import User
from django.contrib.auth.decorators import login_required


TIME_LIMIT = 20 # MINUTES
GRACE_TIME = 2 # SECONDS
PAYMENT_KEYWORD = "Payment"

def list_quizzes(request):
    """
    Display all quizzes for logged-in users.
    """
    quizzes = Quiz.objects.all()
    print(quizzes)
    user = request.user
    if user.is_user:
        full_name = user.username
        email = user.email
    if quizzes.exists():
        return render(request, "instruction.html", {
            "quizzes": quizzes,
            "user_full_name": full_name,
            "user_email": email,
        })
    else:
        return render(request, "no_quizzes.html")

def start_test(request):
    """
    Starts or resumes a quiz for the user.
    """
    user = request.user
    if user.is_user:
        user_id = user.id

    if request.method == "GET":
        return redirect("quiz:list_quizzes")

    # Fetch quizzes and results
    results = Result.objects.filter(user_id=user_id)

    # Check for a running test
    for result in results:
        if result.end_time is None:
            if(now() - result.start_time).total_seconds() <= TIME_LIMIT * 60 + GRACE_TIME: 
                return redirect('quiz:start_question', quiz_id=result.quiz.id, question_id=result.quiz.quiz_questions.first().id)
            else:
                result.end_time = now()
        
    # Start a new quiz
    available_quizzes = Quiz.objects.exclude(id__in=results.values_list('quiz_id', flat=True))
    if not available_quizzes.exists():
        return redirect('quiz:finish_test')

    quiz = available_quizzes.first()
    if(requires_payment(quiz) and not request.user.has_paid):
        return redirect('payment_integration:payment_start')

    request.session["visited_questions"] = []
    
    # Create a new Result object
    result = Result.objects.create(user_id=user_id, quiz=quiz, start_time=now(), user_answers={})

    return redirect('quiz:start_question', quiz_id=quiz.id, question_id=quiz.quiz_questions.first().id)

def start_question(request, quiz_id, question_id):
    """
    Renders a question based on the given IDs.
    """
    quiz = get_object_or_404(Quiz, id=quiz_id)
    question = get_object_or_404(Question, id=question_id)
    answers = question.get_answers()

    # Calculate remaining time
    user = request.user
    if user.is_user:
        user_id = user.id
        full_name = user.username
        email = user.email
    result = get_object_or_404(Result, user_id=user_id, quiz=quiz)
    remaining_time = TIME_LIMIT * 60 - (now() - result.start_time).seconds + GRACE_TIME

    if remaining_time <= 0:
        messages.error(request, "Time limit exceeded")
        return redirect('quiz:quiz_summary', quiz_id=quiz.id)
    
    if "visited_questions" not in request.session:
        request.session["visited_questions"] = []

    if question_id not in request.session["visited_questions"]:
        request.session["visited_questions"].append(question_id)
        request.session.modified = True  # Mark the session as updated

    return render(request, 'question-1.html', {
        'quiz': quiz,
        'question': question,
        'answers': answers,
        'remaining_time': remaining_time,
        'all_question_ids': list(q.id for q in quiz.quiz_questions.all()),
        "visited_questions": request.session["visited_questions"],
    })

def save_answer(request, quiz_id, question_id):
    """
    Saves the user's answer for a question.
    """
    if request.method == "POST":
        selected_answer_id = request.POST.get("selected_answer")

        if not selected_answer_id:
            return redirect('quiz:start_question', quiz_id=quiz_id, question_id=question_id)

        user = request.user
        if user.is_user:
            user_id = user.id
            full_name = user.username
            email = user.email
        quiz = get_object_or_404(Quiz, id=quiz_id)
        question = get_object_or_404(Question, id=question_id)

        # Retrieve the Result object
        result = get_object_or_404(Result, user_id=user_id, quiz=quiz)
        
        remaining_time = TIME_LIMIT * 60 - (now() - result.start_time).seconds + GRACE_TIME
        if remaining_time <= 0:
            messages.error(request, "Time limit exceeded")
            return redirect('quiz:quiz_summary', quiz_id=quiz.id)
    
        # Update the answer in the Result object
        result.user_answers[str(question.id)] = selected_answer_id
        result.save()

        # Determine the next question
        questions = list(quiz.quiz_questions.all())
        current_index = questions.index(question)

        if current_index + 1 < len(questions):
            next_question = questions[current_index + 1]
            return redirect('quiz:start_question', quiz_id=quiz.id, question_id=next_question.id)

        return redirect('quiz:quiz_summary', quiz_id=quiz.id)

    return redirect('quiz:start_question', quiz_id=quiz_id, question_id=question_id)

def quiz_summary(request, quiz_id):
    """
    Displays the quiz summary and calculates the final score.
    """
    user = request.user
    if user.is_user:
        user_id = user.id
        full_name = user.username
        email = user.email
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Fetch the Result object
    result = get_object_or_404(Result, user_id=user_id, quiz=quiz)
    
    # Update the score and end time in the Result object
    result.score = calculate_score(quiz,result)
    if result.score >= result.quiz.score_to_pass:
        result.is_passed = True
    result.end_time = now()
    result.save()

    # Get list of quizzes
    completed_quizzes = []
    
    results = Result.objects.filter(user = user_id)
    for result in results:
        completed_quizzes.append(result.quiz)

    incomplete_quizzes = Quiz.objects.exclude(id__in=results.values_list('quiz_id', flat=True))
    user = request.user

    return render(request, 'start-test.html', {
        "user_full_name" : full_name,
        "email" : user.email,
        "completed_quizzes":completed_quizzes,
        "incomplete_quizzes":incomplete_quizzes
    })

def finish_test(request):
    """
    Renders the finish test template.
    """
    user = request.user
    if user.is_user:
        user_id = user.id
        full_name = user.username
        email = user.email
    user = get_object_or_404(User,id=user_id)
    for quiz in Quiz.objects.all():
        if not Result.objects.filter(quiz=quiz,user=user).first():
            return redirect('quiz:start_test')
            

    tcn = request.user.tcn_number
    return render(request, 'Complete-congrats.html', {'TCN': tcn})

def get_remaining_time(request):
    user = request.user
    if user.is_user:
        user_id = user.id
        full_name = user.username
        email = user.email
    results = Result.objects.filter(end_time__isnull=True,user_id = user_id)
    if results.count() > 1:
        messages.error(request,"Something went wrong")
        return JsonResponse({"error": "Something went wrong"})
    result = results.first()
    if result is None:
        return redirect('quiz:start_test')
    remaining_time = TIME_LIMIT * 60 - (now() - result.start_time).seconds
    if(remaining_time < 0):
        return redirect('quiz:quiz_summary',result.quiz.id)
    return JsonResponse({"time_remaining": remaining_time})

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