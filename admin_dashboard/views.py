from django.shortcuts import render, redirect
from admin_dashboard.models import User 
from django.contrib.auth import authenticate, login
from django.contrib import messages

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

