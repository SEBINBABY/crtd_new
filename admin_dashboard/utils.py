from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from functools import wraps

def role_required(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = []
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            # Redirect to login page or show an error
            return redirect('admin_hr_login')
        return _wrapped_view
    return decorator
