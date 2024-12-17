from django.shortcuts import render, redirect, get_object_or_404
from admin_dashboard.models import User 
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db.models import Q
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
    return render(request, "UpdatedQuestionSection3.html")

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





        




