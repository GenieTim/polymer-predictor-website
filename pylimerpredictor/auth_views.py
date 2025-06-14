from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from .decorators import admin_required
from .forms import (CustomAuthenticationForm, CustomUserCreationForm,
                    UserProfileForm)

User = get_user_model()


@csrf_protect
@require_http_methods(["GET", "POST"])
def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Account created successfully for {user.email}! You can now log in.",
            )
            return redirect("login")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()

    return render(request, "auth/register.html", {"form": form})


@csrf_protect
@require_http_methods(["GET", "POST"])
def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name}!")

                # Redirect to next page if specified, otherwise home
                next_page = request.GET.get("next", "home")
                return redirect(next_page)
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomAuthenticationForm()

    return render(request, "auth/login.html", {"form": form})


@login_required
def logout_view(request):
    """User logout view"""
    user_name = request.user.first_name
    logout(request)
    messages.success(request, f"Goodbye, {user_name}! You have been logged out.")
    return redirect("home")


@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request):
    """User profile view and edit"""
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect("profile")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, "auth/profile.html", {"form": form})


@admin_required
def user_management_view(request):
    """Admin view for managing users"""
    users = User.objects.all().order_by("-created_at")
    return render(request, "auth/user_management.html", {"users": users})


@admin_required
@require_http_methods(["POST"])
def update_user_role(request, user_id):
    """Admin endpoint to update user role"""
    try:
        user = User.objects.get(id=user_id)
        new_role = request.POST.get("role")

        if new_role in dict(User.ROLE_CHOICES):
            old_role = user.role
            user.role = new_role
            user.save()
            messages.success(
                request,
                f"Updated {user.full_name}'s role from {old_role} to {new_role}.",
            )
        else:
            messages.error(request, "Invalid role specified.")
    except User.DoesNotExist:
        messages.error(request, "User not found.")
    except Exception as e:
        messages.error(request, f"Error updating user role: {str(e)}")

    return redirect("user_management")


@admin_required
@require_http_methods(["POST"])
def toggle_user_active(request, user_id):
    """Admin endpoint to activate/deactivate user"""
    try:
        user = User.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()

        status = "activated" if user.is_active else "deactivated"
        messages.success(request, f"User {user.full_name} has been {status}.")
    except User.DoesNotExist:
        messages.error(request, "User not found.")
    except Exception as e:
        messages.error(request, f"Error updating user status: {str(e)}")

    return redirect("user_management")
