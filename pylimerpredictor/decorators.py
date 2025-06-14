from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def role_required(allowed_roles):
    """
    Decorator that checks if user has one of the allowed roles.

    Args:
        allowed_roles: String or list of strings representing allowed roles
                      ('user', 'researcher', 'admin')

    Usage:
        @role_required('admin')
        @role_required(['researcher', 'admin'])
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not hasattr(request.user, "role"):
                raise PermissionDenied("User role not defined")

            if request.user.role not in allowed_roles:
                messages.error(
                    request,
                    f"Access denied. This feature requires {' or '.join(allowed_roles)} role.",
                )
                return redirect("home")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def researcher_required(view_func):
    """Decorator that requires researcher or admin role"""
    return role_required(["researcher", "admin"])(view_func)


def admin_required(view_func):
    """Decorator that requires admin role"""
    return role_required("admin")(view_func)


def user_passes_test_with_message(
    test_func, message="Access denied", redirect_url="home"
):
    """
    Custom version of user_passes_test that shows a message on failure
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not test_func(request.user):
                messages.error(request, message)
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
