from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import *
from django.utils.timezone import now 
from django.contrib import messages
from django.contrib.auth import logout
from django.views.decorators.cache import never_cache
from .utils import *

GRACE_TIME = 5 # SECONDS

@user_only
@never_cache
def exam_instruction(request):
    user = request.user
    return render(request, "exam_instruction.html", { "user_full_name": user.username,"user_email": user.email,})

@user_only
@never_cache
def exam_guidelines(request):
    user = request.user
    return render(request, "exam_guidelines.html", { "user_full_name": user.username,"user_email": user.email,})


@user_only
@never_cache
def automatic_selection(request):
    """
    Display all quizzes for logged-in users.
    """
    quizzes = Quiz.objects.all()
    user = request.user
    if quizzes.exists():
        return render(request, "automatic_selection.html", {
            "quizzes": quizzes,
            "user_full_name": user.username,
            "user_email": user.email,
        })
    else:
        return JsonResponse({"Message":"No quizzes present"})

@user_only
@never_cache
def start_test(request):
    """
    Starts or resumes a quiz for the user.
    """
    if request.method == "GET":
        return redirect("quiz:exam_instruction")

    user = request.user
    if not user.is_user:
        return redirect("users:user_login")
    # Fetch quizzes and results
    results = Result.objects.filter(user_id=user.id)

    # Check for a running test
    for result in results:
        if result.end_time is None:
            if(now() - result.start_time).total_seconds() <= result.quiz.time * 60 + GRACE_TIME: 
                return redirect('quiz:start_question', quiz_id=result.quiz.id, question_id=result.quiz.quiz_questions.first().id)
            else:
                result.end_time = now()
        
    quiz = get_next_quiz(results)
    if not quiz:
        return redirect('quiz:finish_test')
    if(quiz.requires_payment and not request.user.has_paid):
        return redirect('payment_integration:payment_start')

    request.session["marked_questions"] =  []
    request.session.save()
    
    # Create a new Result object
    result = Result.objects.create(user_id=user.id, quiz=quiz, start_time=now(), user_answers={})

    return redirect('quiz:start_question', quiz_id=quiz.id, question_id=quiz.quiz_questions.first().id)

@user_only
@never_cache
def start_question(request, quiz_id, question_id):
    """
    Renders a question based on the given IDs.
    """
    user = request.user
    quiz = get_object_or_404(Quiz, id=quiz_id)
    question = get_object_or_404(Question, id=question_id)
    answers = question.get_answers()

    if(quiz.requires_payment and not request.user.has_paid):
        return render(request,'demo_question.html',{
        'quiz': quiz,
        'question': question,
        'answers': answers,
        'all_question_ids': list(q.id for q in quiz.quiz_questions.all()),
        "is_last_question": (question == quiz.quiz_questions.last()),
        "is_completed": False,
        })

    result = get_object_or_404(Result, user_id=user.id, quiz=quiz)

    if(result.end_time is not None):
        return redirect('quiz:quiz_summary',quiz.id)
    
    remaining_time = quiz.time * 60 - (now() - result.start_time).seconds

    if remaining_time + GRACE_TIME <= 0:
        messages.error(request, "Time limit exceeded")
        return redirect('quiz:quiz_summary', quiz_id=quiz.id)
    
    if "marked_questions" not in request.session:
        request.session["marked_questions"] = []

    selected_answer = None
    if question_id in request.session["marked_questions"]:
        selected_answer = result.user_answers.get(str(question_id))
    
    request.session.save()
    return render(request, 'question-1.html', {
        'quiz': quiz,
        'question': question,
        'answers': answers,
        'remaining_time': remaining_time,
        'all_question_ids': list(q.id for q in quiz.quiz_questions.all()),
        "marked_questions": request.session["marked_questions"],
        "unmarked_questions": quiz.quiz_questions.count() - len(request.session["marked_questions"]),
        "user_full_name":user.username,
        "user_email":user.email,
        "selected_answer": selected_answer,
        "is_last_question": (question == quiz.quiz_questions.last()),
        "is_completed": (len(result.user_answers) == quiz.quiz_questions.count()),
    })

@user_only
def save_answer(request, quiz_id, question_id):
    """
    Saves the user's answer for a question.
    """
    if request.method == "POST":
        user = request.user
        selected_answer_id = request.POST.get("selected_answer")
        quiz = get_object_or_404(Quiz, id=quiz_id)
        question = get_object_or_404(Question, id=question_id)
        result = get_object_or_404(Result, user_id=user.id, quiz=quiz)
        remaining_time = result.quiz.time * 60 - (now() - result.start_time).seconds

        if not selected_answer_id and remaining_time > 0:
            return redirect('quiz:start_question', quiz_id=quiz_id, question_id=question_id)

        
        if(result.end_time is not None):
            return redirect('quiz:quiz_summary', quiz_id=quiz.id)
        
        remaining_time = quiz.time * 60 - (now() - result.start_time).seconds + GRACE_TIME
        if remaining_time <= 0:
            messages.error(request, "Time limit exceeded")
            return redirect('quiz:quiz_summary', quiz_id=quiz.id)
    
        # Update the answer in the Result object
        result.user_answers[str(question.id)] = selected_answer_id
        result.save()
        if question_id not in request.session["marked_questions"]:
            request.session["marked_questions"].append(question_id)
            request.session.save()

        # Determine the next question
        questions = list(quiz.quiz_questions.all())
        current_index = questions.index(question)

        if current_index + 1 < len(questions):
            next_question = questions[current_index + 1]
            return redirect('quiz:start_question', quiz_id=quiz.id, question_id=next_question.id)
        
        if(remaining_time <= 0):
            return redirect('quiz:quiz_summary',result.quiz.id)
        else:
            return redirect('quiz:start_question', quiz_id=quiz_id, question_id=question_id)

    return redirect('quiz:start_question', quiz_id=quiz_id, question_id=question_id)

@user_only
def quiz_summary(request, quiz_id):
    """
    Displays the quiz summary and calculates the final score.
    """
    user = request.user
    if not user.is_user:
        return redirect("users:user_login")
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Fetch the Result object
    result = get_object_or_404(Result, user_id=user.id, quiz=quiz)
    
    # Update the score and end time in the Result object
    result.score = calculate_score(quiz,result)
    if result.score >= result.quiz.score_to_pass:
        result.is_passed = True
    result.end_time = now()
    result.save()

    # Get list of quizzes
    completed_quizzes = []
    
    results = Result.objects.filter(user = user.id)
    for result in results:
        completed_quizzes.append(result.quiz)

    incomplete_quizzes = Quiz.objects.exclude(id__in=results.values_list('quiz_id', flat=True))
    request.session["marked_questions"] = []
    request.session.save()

    return render(request, 'start-test.html', {
        "user_full_name" : user.username,
        "user_email" : user.email,
        "completed_quizzes":completed_quizzes,
        "incomplete_quizzes":incomplete_quizzes
    })
    

@user_only
def finish_test(request):
    """
    Renders the finish test template.
    """
    user = request.user
    if not user.is_user:
        return redirect("users:user_login")
    user.is_verified = True
    user.save()
    for quiz in Quiz.objects.all():
        if not Result.objects.filter(quiz=quiz,user=user).first():
            return redirect('quiz:start_test')

    tcn = request.user.tcn_number
    return render(request, 'Complete-congrats.html', {'TCN': tcn,'last': Quiz.objects.last().id})

@user_only
def get_remaining_time(request):
    user = request.user
    results = Result.objects.filter(end_time__isnull=True,user = user)
    if results.count() > 1:
        messages.error(request,"Something went wrong")
        return JsonResponse({"error": "Something went wrong"})
    result = results.first()
    if result is None:
        quiz = Result.objects.filter(user = user).last().quiz
        if quiz:
            return redirect('quiz:quiz_summary',quiz.id)
        else:
            return redirect('quiz:start_test')
    remaining_time = result.quiz.time * 60 - (now() - result.start_time).seconds
    if(remaining_time <= 0):
        return redirect('quiz:quiz_summary',result.quiz.id)
    return JsonResponse({"time_remaining": remaining_time})

@user_only
def end_test(request):
    user = request.user
    for result in Result.objects.filter(user=user):
        if not result.end_time: result.end_time = now()
        result.is_passed = False
        result.score = 0
        result.save()
    for quiz in Quiz.objects.all():
        if not Result.objects.filter(user=user,quiz=quiz).exists():
            result = Result(user=user,quiz=quiz,score=0,end_time=now())
            result.save()
    messages.error(request, "You violated our terms and are disqualified from the test.")
    logout(request)
    return redirect('users:verify_passkey')