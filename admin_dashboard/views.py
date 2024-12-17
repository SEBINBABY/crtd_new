from django.shortcuts import render, redirect, get_object_or_404
from admin_dashboard.models import User 
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse

from quiz.models import Quiz,Question,Answer
from .utils import role_required
from users.models import Passkey

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
                return redirect('admin_dashboard:dashboard')  # Shared dashboard for both roles
            else:
                messages.error(request, "Access restricted to Admin and HR Staff only.")
        else:
            messages.error(request, "Invalid email or password.")  
    return render(request, 'admin_login.html')

# @role_required(allowed_roles=['admin', 'hr_staff'])
def question_section(request):
    return render(request, "UpdatedQuestionSection3.html",
                  {"user":request.user,
                   "quizzes":Quiz.objects.all()})

def question_list(request,quiz_id):
    return render(request,'question_list.html',
                  {"user":request.user,
                   "quiz":get_object_or_404(Quiz,id=quiz_id)})

def add_question(request):
    if not request.POST:
        return redirect("admin_dashboard:question_section")
    
    data = request.POST.get('data',None)
    if not data: return JsonResponse({"error":"No form data"})

    quiz_id = data.get('quiz_id')
    question_text = data.get('question_text',None)
    if not question_text: JsonResponse({"error":"No question"})

    correct_answer_id  = data.get('correct_answer_id',None)
    if not correct_answer_id: return JsonResponse({"error":"Must select correct answer"})
        
    answers_data = []
    answer_id = data.get('answer-1',None)
    while(answer_id is not None):
        answer_text = data.get(f'answer_text-${answer_id}')
        answers_data.append([answer_text,answer_id==correct_answer_id])

    if len(answers_data) < 2: return JsonResponse({"error": "Atleast 2 answers required"})
    
    question = Question(question_text=question_text, quiz_id=quiz_id)
    question.save()
    for data in answers_data:
        answer = Answer(answer_text = data[0],is_correct=data[1],question_id=question.id)
        answer.save()
    
    return redirect('admin_dashboard:question_list',quiz_id)

def edit_question(request):
    if not request.POST:
        return redirect("admin_dashboard:question_section")
    
    data = request.POST.get('data',None)
    if not data: return JsonResponse({"error":"No form data"})

    quiz_id = data.get('quiz_id')
    question_id = data.get('question_id')
    question_text = data.get('question_text',None)
    if not question_text: JsonResponse({"error":"No question"})

    correct_answer_id  = data.get('correct_answer_id',None)
    if not correct_answer_id: return JsonResponse({"error":"Must select correct answer"})
        
    answers_data = []
    answer_id = data.get('answer-1',None)
    while(answer_id is not None):
        answer_text = data.get(f'answer_text-${answer_id}')
        answers_data.append([answer_text,answer_id==correct_answer_id])

    if len(answers_data) < 2: return JsonResponse({"error": "Atleast 2 answers required"})
    
    question = get_object_or_404(Question,id = question_id)
    question.save()
    new_answer_ids = []
    for data in answers_data:
        answer, created = Answer.objects.get_or_create(answer_text = data[0],is_correct=data[1],question_id=question.id)
        new_answer_ids.append(answer.id)
        answer.save()
    
    for answer in Answer.objects.filter(question_id=question.id):
        if answer.id not in new_answer_ids:
            answer.delete()
    
    return redirect('admin_dashboard:question_list',quiz_id)
        
def delete_question(request,question_id):
    question = get_object_or_404(Question,id=question_id)
    quiz_id = question.quiz.id
    answers = Answer.objects.filter(question_id = question_id)
    for answer in answers:
        answer.delete()
    question.delete()

    return redirect('admin_dashboard:question_list',quiz_id)


# @role_required(allowed_roles=['admin', 'hr_staff'])
def user_list(request):
    query = request.GET.get('query', '')  # Get the search query
    users = User.objects.all()
    filter_date = request.GET.get('filter_date') # Single date for filtering
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
        key_value = request.POST.get("key", "CRTD@2025")  # Default if not provided    
        passkey = Passkey.objects.create(key=key_value, is_active=True)
        messages.success(request, f"Passkey '{passkey.key}' added successfully!") 
    return render(request, "passkey.html")  # Render a form template  

# For Edit button in Passkey Modal
def update_passkey(request, passkey_id):
    if request.method == "POST":
        key_value = request.POST.get("key", "CRTD@2025")  # Get key from request or use default
        # Update the passkey instance with new key and set is_active=True
        Passkey.objects.filter(id=passkey_id).update(key=key_value, is_active=True)
        messages.success(request, f"Passkey '{passkey.key}' added successfully!") 
    passkey = get_object_or_404(Passkey, id=passkey_id)
    return render(request, "passkey.html", {"passkey": passkey})

def delete_passkey(request, passkey_id):
    key_value = Passkey.objects.filter(id=passkey_id)
    key_value.delete()
    return redirect("admin_dashboard:passkey")

    """
    <form method="post" action="{% url 'delete_passkey' passkey.id %}">
    {% csrf_token %}
    <button type="submit">Yes, Delete</button>
    <a href="{% url 'passkey_list' %}">Cancel</a>
    </form>
    """





        




