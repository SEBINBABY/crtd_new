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
    """
    Renders the exam instruction template.
    """
    if request.user.is_verified: return redirect('quiz:finish_test')
    if(is_test_started(request)): return redirect('quiz:disqualify')
    return render(request, "exam_instruction.html")

@user_only
@never_cache
def exam_guidelines(request):
    """
    Renders the exam guidelines template.
    """
    if request.user.is_verified: return redirect('quiz:finish_test')
    if(is_test_started(request)): return redirect('quiz:disqualify')
    return render(request, "exam_guidelines.html")


@user_only
@never_cache
def automatic_selection(request):
    """
    Renders the template which lists all the quizzes to the user before the test starts.
    """
    if request.user.is_verified: return redirect('quiz:finish_test')
    if(is_test_started(request)): return redirect('quiz:disqualify')
    quizzes = Quiz.objects.all()
    if quizzes.exists():
        return render(request, "automatic_selection.html", {"quizzes": quizzes})
    else:
        return JsonResponse({"Message":"No quizzes present"})

@user_only
@never_cache
def start_test(request):
    """
    Starts the quiz for the user.
    """
    if request.method == "GET":
        return redirect("quiz:exam_instruction")

    user = request.user
    
    """FOR REMOVAL! Leaving it commented for now to test if something breaks

    # Check for a running test
    for result in results:
        if result.end_time is None:
            if(now() - result.start_time).total_seconds() <= result.quiz.time * 60: 
                return redirect('quiz:start_question', quiz_id=result.quiz.id, question_id=result.quiz.quiz_questions.first().id)
            else:
                result.end_time = now() 
    """
        
    quiz = get_next_quiz(user.id)
    if not quiz:
        return redirect('quiz:finish_test')
    if(quiz.requires_payment and not user.has_paid):
        return redirect('payment_integration:payment_start')

    request.session["marked_questions"] =  []
    request.session.save()
    
    # Create a new empty Result object for the next quiz
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

    # if the user visited this view through the buttons in the payment_second template, 
    # load the demo template that doesn't allow answering of the questions
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

    # redirect to quiz summary if quiz already submitted
    if(result.end_time is not None):
        return redirect('quiz:quiz_summary',quiz.id)
    
    #remaining_time = quiz.time * 60 - (now() - result.start_time).seconds
    

    remaining_time = result.get_remaining_time()
    if remaining_time + GRACE_TIME <= 0:
        messages.error(request, "Time limit exceeded")
        return redirect('quiz:quiz_summary', quiz_id=quiz.id)
    
    if "marked_questions" not in request.session:
        request.session["marked_questions"] = []

    selected_answer = None
    if question_id in request.session["marked_questions"]:
        selected_answer = result.user_answers.get(str(question_id))
    
    request.session.save()
    first_unmarked = quiz.quiz_questions.exclude(id__in = request.session["marked_questions"]).first()
    if first_unmarked:
        first_unmarked_id = first_unmarked.id
    else:
        first_unmarked_id = quiz.quiz_questions.last().id

    return render(request, 'question-1.html', {
        'quiz': quiz,
        'question': question,
        'answers': answers,
        'remaining_time': remaining_time,
        'formatted_remaining_time': f"{(remaining_time//60):02d}:{(remaining_time%60):02d}",
        'all_question_ids': list(q.id for q in quiz.quiz_questions.all()),
        "marked_questions": request.session["marked_questions"],
        "unmarked_questions": quiz.quiz_questions.count() - len(request.session["marked_questions"]),
        "user_full_name":user.username,
        "user_email":user.email,
        "selected_answer": selected_answer,
        "first_unmarked_question": first_unmarked_id,
        "is_last_question": (question == quiz.quiz_questions.last()),
        "is_completed": (len(result.user_answers) == quiz.quiz_questions.count()),
        "is_first_question": (question == Quiz.objects.first().quiz_questions.first())
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
        remaining_time = result.get_remaining_time()

        if not selected_answer_id and remaining_time > 0:
            return redirect('quiz:start_question', quiz_id=quiz_id, question_id=question_id)

        
        if(result.end_time is not None):
            return redirect('quiz:quiz_summary', quiz_id=quiz.id)
        
        remaining_time = result.get_remaining_time()
        if remaining_time + GRACE_TIME <= 0:
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
@never_cache
def quiz_summary(request, quiz_id):
    """
    Displays the quiz summary and calculates the final score.
    """

    user = request.user
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Fetch the Result object
    result = get_object_or_404(Result, user_id=user.id, quiz=quiz)
    
    if result.end_time is not None:
        return redirect("quiz:disqualify")
    result.end_time = now()
    result.save()

    # Get list of quizzes
    completed_quizzes = []
    
    results = Result.objects.filter(user = user.id).order_by('quiz__order')
    for result in results:
        completed_quizzes.append(result.quiz)
    
    incomplete_quizzes = Quiz.objects.exclude(id__in=results.values_list('quiz_id', flat=True))
    request.session["marked_questions"] = []
    request.session.save()
    
    if request.session.get("finished_test") == True:
        return redirect('quiz:finish_test')
    
    if incomplete_quizzes.count() == 0:
        user.is_verified = True
        user.save()
    
    return render(request, 'start-test.html', {
        "user_full_name" : user.username,
        "user_email" : user.email,
        "completed_quizzes":completed_quizzes,
        "incomplete_quizzes":incomplete_quizzes,
        "total_quizzes" : Quiz.objects.count(),
    })

@user_only
def finish_test(request):
    """
    Renders the finish test template.
    """
    request.session["finished_test"] = True

    tcn = request.user.tcn_number
    return render(request, 'Complete-congrats.html', {'TCN': tcn})

@user_only
def get_remaining_time(request):
    user = request.user
    results = Result.objects.filter(end_time__isnull=True,user = user)
    if results.count() > 1:
        print(results)
        return JsonResponse({"error": "Something went wrong"})
    result = results.first()
    if result is None:
        quiz = Result.objects.filter(user = user).last().quiz
        if quiz:
            return redirect('quiz:quiz_summary',quiz.id)
        else:
            return redirect('quiz:exam_instruction')
    remaining_time = result.get_remaining_time()
    if(remaining_time <= 0):
        return redirect('quiz:quiz_summary',result.quiz.id)
    return JsonResponse({"time_remaining": remaining_time})
            
@user_only
def disqualify(request):
    user = request.user
    if user.is_verified:
        logout(request)
        return redirect("users:user_login")
    for result in Result.objects.filter(user=user,end_time__isnull=True):
        result.end_time = now()
        result.save()
    messages.error(request, "You have been disqualified due to non-compliance with the test guidelines.")
    user.is_verified = False
    user.is_qualified = False
    user.save()
    logout(request)
    if request.method == "POST":
        return JsonResponse({"message":"You have been disqualified due to non-compliance with the test guidelines."})
    return redirect("users:user_login")