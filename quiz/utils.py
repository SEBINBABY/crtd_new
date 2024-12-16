from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from functools import wraps
from admin_dashboard.models import User

def user_only(view_func):
    @wraps(view_func)
    @login_required(login_url="/user_login")
    def _wrapped_view(request, *args, **kwargs):
        if request.user.role != User.USER:
            return view_func(request, *args, **kwargs)
        # Redirect to login page or show an error
        return redirect('users:user_login')
    return _wrapped_view

