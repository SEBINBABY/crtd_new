from django.shortcuts import render, redirect, get_object_or_404
from admin_dashboard.models import User 
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse

from quiz.models import Quiz,Question,Answer
from .utils import role_required
from users.models import Passkey
from .models import Amount
import datetime

# @role_required(allowed_roles=['admin', 'hr_staff'])
def dashboard(request):
    # Fetch all user objects
    users = User.objects.filter(role=User.USER)   
    # Check if users were retrieved
    if not users.exists():
        # If no users exist, display a relevant message
        title = "No Users Found"
        context = {
            "users": None,
            "title": title,
        }
    else:
        # If users exist, display them
        title = "All Users"
        context = {
            "users": users,
            "title": title,
        }
    return render(request, 'dashboard.html', context)

def dashboard_home(request):
    total_users = User.objects.filter(role=User.USER).count()
    today_users = User.objects.filter(created_at__date = datetime.date.today(),role=User.USER).count()
    total_submitted_users = User.objects.filter(role=User.USER, is_verified = True).count()
    today_submitted_users = User.objects.filter(role=User.USER, is_verified = True,created_at__date = datetime.date.today()).count()
    total_not_submitted_users = total_users - total_submitted_users
    today_not_submitted_users = today_users - today_submitted_users
    today = datetime.date.today().__format__('%Y-%m-%d')
    return render(request, 'AccountSidebar.html', 
                  {'user':request.user,
                   'total_users': total_users,
                   'today_users': today_users,
                   'total_submitted_users': total_submitted_users,
                   'today_submitted_users': today_submitted_users,
                   'total_not_submitted_users': total_not_submitted_users,
                   'today_not_submitted_users': today_not_submitted_users,
                   'today': today,})

def get_user_results(request,user_id):
    requested_user = get_object_or_404(User,id=user_id)

    correct_answer_counts = {}
    user_results = requested_user.user_results.all()
    for result in user_results:
        correct_answer_count = 0
        quiz_id = result.quiz.id
        for answer_id in result.user_answers.values():
            answer = get_object_or_404(Answer,id=answer_id)
            if correct_answer_counts.get(str(quiz_id),None) is None:
                correct_answer_counts[str(quiz_id)] = 0
            if answer.is_correct:            
                correct_answer_count += 1
        correct_answer_counts[str(quiz_id)] = correct_answer_count

    return JsonResponse({'requested_user_name':requested_user.username,
                         'correct_answer_counts':correct_answer_counts,
                         'quizzes': list(map(Quiz.serialize,Quiz.objects.all())),
                         'total_quizzes': Quiz.objects.count(),
                         })



# @role_required(allowed_roles=['admin', 'hr_staff'])
def filtered_users(request, status):
    if status == "submitted":
        users = User.objects.filter(is_verified=True, role=User.USER)
        title = "Submitted Users"
    elif status == "not_submitted":
        users = User.objects.filter(is_verified=False, role=User.USER)
        title = "Not Submitted Users"
    else:
        users = User.objects.filter(role=User.USER)
        title = "All Users"

    context = {
        "users": users,
        "title": title,
    }
    return render(request, "dashboard.html", context)

def admin_hr_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        # Authenticate user
        user = authenticate(request, email=email, password=password)
        if user:
            # Check if the user is admin or hr_staff
            if user.role in [User.ADMIN, User.HR_STAFF]:
                # Log the user in
                login(request, user)
                return redirect('admin_dashboard:dashboard_home')  # Shared dashboard for both roles
            else:
                messages.error(request, "Access restricted to Admin and HR Staff only.")
        else:
            messages.error(request, "Invalid email or password.")  
    return render(request, 'admin_login.html')

# @role_required(allowed_roles=['admin', 'hr_staff'])
def question_section(request):
    return render(request, "quiz_list.html",
                  {"user":request.user,
                   "quizzes":Quiz.objects.all()})

def question_list(request,quiz_id):
    quiz = get_object_or_404(Quiz,id=quiz_id)
    return render(request,'question_list.html',
                  {"user":request.user,
                   "quiz": quiz,
                   })

def add_question(request):
    if not request.POST:
        return redirect("admin_dashboard:question_section")

    data = request.POST
    
    quiz_id = data.get('quiz_id')
    question_text = data.get('question_text',None)
    if not question_text: JsonResponse({"error":"No question"})

    correct_answer_id  = data.get('correct_answer_id',None)
    if not correct_answer_id: return JsonResponse({"error":"Must select correct answer"})
    correct_answer_id = int(correct_answer_id)

    answers_data = []
    # answer id refers to the id from the front end NOT the object id.
    for answer_id in range(1,5):
        answer_text = data.get(f'answer_text-{answer_id}')
        if answer_text == '':
            break;
        answers_data.append([answer_text,answer_id==correct_answer_id])

    if len(answers_data) < 2: return JsonResponse({"error": "Atleast 2 answers required"})

    question = Question(question_text=question_text, quiz_id=quiz_id)
    question.save()
    for data in answers_data:
        answer = Answer(answer_text = data[0],is_correct=data[1],question_id=question.id)
        answer.save()

    return redirect('admin_dashboard:question_list',quiz_id)

def edit_question(request):
    if request.GET:
        question_id= request.GET.get('question_id')
        question = get_object_or_404(Question,id=question_id)
        index = 1
        for q in question.quiz.quiz_questions.all():
            if q.id == question.id:
                break
            index += 1
        return JsonResponse({
            "question": question.serialize(),
            "answers": list(map(Answer.serialize,question.answers_for_question.all())),
            "index": index,
        })
    
    elif request.POST:
        data = request.POST

        question_id = data.get('question_id')
        question_text = data.get('question_text',None)
        if not question_text: JsonResponse({"error":"No question"})

        correct_answer_id  = data.get('correct_answer_id',None)
        if not correct_answer_id: return JsonResponse({"error":"Must select correct answer"})
        answer_ids = data.get('answer_ids',None)
        answer_ids = list(answer_ids.split(','))[:-1]
        
        answers_data = []
        for answer_id in answer_ids:
            answer_text = data.get(f'answer_text-{answer_id}')
            if(answer_text == ''): break
            answers_data.append([answer_text,answer_id==correct_answer_id])

        if len(answers_data) < 2: return JsonResponse({"error": "Atleast 2 answers required"})

        question = get_object_or_404(Question,id = question_id)
        question.question_text = question_text
        new_answer_ids = []
        for data in answers_data:
            answer, created = Answer.objects.get_or_create(answer_text = data[0],is_correct=data[1],question_id=question.id)
            new_answer_ids.append(answer.id)
            answer.save()

        question.save()
        for answer in Answer.objects.filter(question_id=question.id):
            if answer.id not in new_answer_ids:
                answer.delete()

        return redirect('admin_dashboard:question_list',question.quiz.id)

def delete_question(request):
    if request.POST:
        question_id = request.POST.get('question_id')
        if question_id is None: return JsonResponse({"error":"No question ID provided"})
        question = get_object_or_404(Question,id = question_id)
        quiz_id = question.quiz.id
        question.delete()

        return redirect('admin_dashboard:question_list',quiz_id)


# @role_required(allowed_roles=['admin', 'hr_staff'])
def user_list(request):
    query = request.GET.get('query', '')  # Get the search query
    users = User.objects.all()
    filter_date = request.GET.get('filter_date') # Single date for filtering
    submitted = request.GET.get('submitted')
    if query:
        users = users.filter(
            Q(username__icontains=query) |  # Full name search (using username)
            Q(email__icontains=query) |    # Email search
            Q(contact_number__icontains=query) |  # Contact number search
            Q(tcn_number__icontains=query) |  # TCN number search
            Q(created_at__icontains=query)  # Account creation date search
        )
    # Apply date filtering
    if filter_date:
        users = users.filter(created_at__date=filter_date, role=User.USER)  # Compare with the date part of created_at
    if submitted == 'True':
        users = users.filter(is_verified=True)
    elif submitted == 'False':
        users = users.filter(is_verified=False)

    return render(request, 'dashboard.html', {'users': users, 'query': query})

def passkey(request):   # Once user click Passkey Section
    # Fetch all passkey objects
    passkeys = Passkey.objects.all() 
    # Check if the queryset is empty, set to None if empty
    if not passkeys.exists():
        passkeys = None   
    # Pass the data to the template
    return render(request, "passkey.html", {"passkeys": passkeys})

def add_passkey(request):  # For Save button in Add Passkey Modal
    if request.method == "POST":
        key_value = request.POST.get("key")      
        passkey = Passkey.objects.create(key=key_value, is_active=True)
        messages.success(request, f"Passkey '{passkey.key}' added successfully!") 
        return redirect("admin_dashboard:passkey") 
    passkeys = Passkey.objects.all()
    return render(request, "passkey.html", {"passkeys": passkeys})
  

# For Edit button in Passkey Modal
def update_passkey(request, passkey_id):
    passkey = get_object_or_404(Passkey, id=passkey_id)
    if request.method == "POST":
        key_value = request.POST.get("key")
        if key_value:
            passkey.key = key_value
            passkey.is_active = True  # Optional: Update other fields if needed
            passkey.save()
            messages.success(request, "Passkey updated successfully!")
        else:
            messages.error(request, "Passkey cannot be empty.")
        return redirect("admin_dashboard:passkey")
    passkeys = Passkey.objects.all()
    return render(request, "passkey.html", {"passkeys": passkeys})


def delete_passkey(request, passkey_id):
    if request.method == "POST":
        passkey = get_object_or_404(Passkey, id=passkey_id)
        passkey.delete()
        return redirect('admin_dashboard:passkey')  

def amount_section(request):
    if request.POST:
        amount = request.POST.get('amount',None)
        if amount is None: return JsonResponse({"error":"Enter an amount"})
        Amount.set_value(int(amount))
        return redirect("admin_dashboard:amount_section")

    return render(request, "Amount-Edit.html",{
        'amount': Amount.get_value()
    })