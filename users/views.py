from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Passkey
from admin_dashboard.models import User
from .models import OTP
import random
from django.core.mail import send_mail
from django.conf import settings
from django.utils.timezone import now
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
import re
from django.contrib.auth import authenticate, login, logout
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.views import PasswordResetView, PasswordResetCompleteView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.views.decorators.cache import never_cache

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
@never_cache
def verify_passkey(request):
    if request.method == "POST":
        passkey = request.POST.get("passkey")
        if Passkey.objects.filter(key=passkey, is_active=True).exists():
            return redirect("users:user_login")
        else:
            messages.error(request, "Invalid Passkey!")
    return render(request, "verify_passkey.html")

# User can submit the username and email for email verification
@never_cache
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
            return render(request, "register_verified.html", {
                'full_name': username,
                'email': email,
                'contact_number': contact_number
            })
        # Validate password strength
        password_error = is_valid_password(password)
        if password_error:
            messages.error(request, password_error)
            return render(request, "register_verified.html", {
                'full_name': username,
                'email': email,
                'contact_number': contact_number
            })
        if User.objects.filter(email=email).exists():
            messages.error(request, "This Email is already registered!")
            return render(request, "register_verified.html", {
                'full_name': username,
                'email': email,
                'contact_number': contact_number
            })
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
                return render(request, "register_verified.html", {
                'full_name': username,
                'email': email,
                'contact_number': contact_number
            })
        except OTP.DoesNotExist:
            messages.error(request, "Email verification is required!")
            return render(request, "register_verified.html", {
                'full_name': username,
                'email': email,
                'contact_number': contact_number
            })
    return render(request, "register_verified.html", {
                'full_name': username,
                'email': email,
                'contact_number': contact_number})

# Login functionality for authentication
@never_cache
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
                request.session['email'] = email
                # Redirect to the desired page after login
                return redirect("quiz:exam_instruction")
            else:
                messages.error(request, "Access restricted to Users Only.")
                return render(request, "login.html")  # Ensure response is returned
        else:
            messages.error(request,"Invalid Email id or Password!")
            return render(request, "login.html")  # Ensure response is returned
    else:
        return render(request, "login.html")

# Logout functionality for USER role
def user_logout(request):
    if request.user.is_authenticated and request.user.role == User.USER:
        # Clear the session and log out the user
        logout(request)
        messages.success(request, "You have been successfully logged out.")
        return redirect('users:verify_passkey') # Redirect to the login page
    else:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('users:verify_passkey')  # Redirect to the login page

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
        otp_code = random.randint(1000, 9999)
        # Delete old OTPs for the email
        otps = OTP.objects.filter(email=email)
        otps.delete()
        # Save or update the OTP
        OTP.objects.create(email=email, full_name=username, otp_code=otp_code)
        # Send OTP email
        # Split OTP into individual characters
        otp_digits = list(str(otp_code))  # ['2', '4', '6', '8']
        context = {"otp_digits": otp_digits, "name":username} #  OR
        #context = {"otp_code": otp_code, "name":username}
        email_subject = "Email Verification Code"
        email_body = render_to_string("email_message.txt", context)
        email_html = render_to_string("email.html", context)
        send_mail(
            email_subject,
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
            html_message=email_html
        )
        messages.success(request, "OTP sent successfully! Please check your registered mail.")
        return render(request,"otp.html")
    messages.error(request, "Invalid request method!")

# Redirection to OTP Page for the submission of OTP
def otp_page(request):
    return render(request, "otp.html")
  
# View to handle OTP Verification
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
    

# Class based views for handling the forgot password
# Created a custom form to validate the email field.
class CustomPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("This account doesn't exist. Please create an account first.")
        return email

 #  Will take the user to a page to enter his mail id and submit the same  
class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'password_reset.html'
    email_template_name = 'password_reset_email.html'
    form_class = CustomPasswordResetForm
    success_url = reverse_lazy('users:user_login')

    def form_valid(self, form):
        messages.add_message(
            self.request,
            messages.SUCCESS,
            "We have emailed you the steps to reset your password. Please check your inbox and follow the steps provided."
        )
        return super().form_valid(form)


# After receiving the mail, user will be landed to this page to confirm his New Passsword
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_reset_confirm.html'  # Set your custom template name
    # Override success_url attribute
    success_url = reverse_lazy('users:password_reset_complete')


# # Once the New Password is set, user will be taken back to this user_login page
# class CustomPasswordResetCompleteView(PasswordResetCompleteView):
#     # Override the get method to redirect directly
#     def get(self, request, *args, **kwargs):
#         return redirect(reverse_lazy('users:user_login'))


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'password_reset_complete.html'  # Set your custom template name
    # Override success_url attribute
    success_url = reverse_lazy('users:user_login')

    

    

