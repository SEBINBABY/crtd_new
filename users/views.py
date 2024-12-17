from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Passkey
from admin_dashboard.models import User
from .models import OTP
import random
from django.core.mail import send_mail
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
import re
from django.contrib.auth import authenticate, login 

# Password validation function
def is_valid_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must contain at least one special character."
    return None  # No issues

# To verify passkey entered by user
def verify_passkey(request):
    if request.method == "POST":
        passkey = request.POST.get("passkey")
        if Passkey.objects.filter(key=passkey, is_active=True).exists():
            return redirect("users:user_login")
        else:
            messages.error(request, "Invalid Passkey!")
    return render(request, "verify_passkey.html")

# User can submit the username and email for email verification
def register(request):
    return render(request, 'register.html')

# Once the email is verified, User will be registered in the User model
def register_verified(request):
    if request.method == "POST":
        username = request.POST.get("full_name")
        email = request.POST.get("email")
        contact_number = request.POST.get("contact_number")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect("users:register_verified")
        # Validate password strength
        password_error = is_valid_password(password)
        if password_error:
            messages.error(request, password_error)
            return redirect("users:register_verified")
        if User.objects.filter(email=email).exists():
            messages.error(request, "This Email is already registered!")
            return redirect("users:register_verified")
        # Ensure the email has been verified before creating the user
        try:
            otp_instance = OTP.objects.get(email=email)
            if not otp_instance.is_expired():
                # Email verified, proceed with registration
                user = User.objects.create_user(
                    username=username.strip(),
                    email=email.strip(),
                    contact_number=contact_number,
                    password=password,
                )
                user.is_email_verified = True
                user.save()
                return render(request, "create_account_success.html")
            else:
                messages.error(request, "OTP has expired! Please verify email again.")
                return redirect("users:register_verified")
        except OTP.DoesNotExist:
            messages.error(request, "Email verification is required!")
            return redirect("users:register_verified")
    return render(request, "register_verified.html")

# Login functionality for authentication
def user_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        # Authenticate the user
        user = authenticate(request, email=email, password=password)
        if user:
            # Check if the user is IN USER Role itself, Not admin or hr_staff
            if user.role == User.USER:
            # Successfully authenticated, log the user in
                login(request, user)
                # Redirect to the desired page after login
                return redirect("quiz:list_quizzes")
            else:
                messages.error(request, "Access restricted to Users Only.")
        else:
            # Invalid credentials, show an error message
            messages.error(request, "Invalid email or password!")
    return render(request, "login.html")

# View to send OTP
@csrf_exempt
def send_email_verification_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("full_name")
        if not email:
            messages.error(request, "Email is required!") 
            return redirect("users:register")
        if User.objects.filter(email=email).exists():
            messages.error(request, "This Email is already registered!")
            return redirect("users:register")
        request.session["email_for_otp"] = email  # Save email to session -check
        request.session["full_name"] = username  # Save username to session - check
        otp_code = random.randint(1000, 9999)
        # Delete old OTPs for the email
        otps = OTP.objects.filter(email=email)
        otps.delete()
        # Save or update the OTP
        OTP.objects.create(email=email, full_name=username, otp_code=otp_code)
        # Send OTP email
        context = {"otp_code": otp_code, "name":username}
        email_subject = "Email Verification Code"
        email_body = render_to_string("email_message.txt", context)
        send_mail(
            email_subject,
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        messages.success(request, "OTP sent successfully! Please check your registered mail.")
        return render(request,"otp.html")
    messages.error(request, "Invalid request method!")

def otp_page(request):
    return render(request, "otp.html")
  

@csrf_exempt
def verify_email_otp(request):
    if request.method == "POST":
        # Collect the concatenated OTP
        otp_code = (
            request.POST.get("otp1", "") +
            request.POST.get("otp2", "") +
            request.POST.get("otp3", "") +
            request.POST.get("otp4", "")
        )

        if not otp_code:
            # If OTP is not entered, display an error and stay on the OTP page
            messages.error(request, "OTP is required!")
            return redirect("users:otp_page")

        try:
            # Retrieve OTP instance based on the entered OTP
            otp_instance = OTP.objects.get(otp_code=otp_code)
            if otp_instance.is_expired():
                # If the OTP has expired, redirect to registration with an error
                messages.error(request, "OTP has expired!")
                return redirect("users:register")

            # If the OTP is correct, verify the user's email
            email = otp_instance.email
            full_name = otp_instance.full_name

            try:
                user = User.objects.get(email=email)
                user.is_email_verified = True
                user.save()
            except User.DoesNotExist:
                pass  # Continue even if user doesn't exist for now

            # Render the next registration step
            context = {
                "email": email,
                "full_name": full_name,
                "is_verified": True,
            }
            messages.success(request, "Email verified successfully! Proceed with registration.")
            return render(request, "register_verified.html", context)

        except OTP.DoesNotExist:
            # If OTP is not found in the database, stay on the OTP page
            messages.error(request, "Invalid OTP")
            return redirect("users:otp_page")

    else:
        # Handle invalid request methods
        messages.error(request, "Invalid request method!")
        return redirect("users:register")
    

    

