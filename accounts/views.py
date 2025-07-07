from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from .forms import UserRegistrationForm, UserProfileForm, CustomPasswordChangeForm, AdminUserEditForm
import uuid

User = get_user_model()

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Send verification email (mock)
            send_verification_email(user)
            messages.success(request, 'Registration successful! Please check your email to verify your account.')
            return redirect('accounts:login')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def send_verification_email(user):
    """Mock email verification"""
    subject = 'Verify Your Account'
    message = f'Click the link to verify your account: http://localhost:8000/verify/{user.verification_token}/'
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

def verify_email(request, token):
    try:
        user = User.objects.get(verification_token=token)
        user.is_verified = True
        user.save()
        messages.success(request, 'Your account has been verified successfully!')
        return redirect('accounts:login')
    except User.DoesNotExist:
        messages.error(request, 'Invalid verification token.')
        return redirect('accounts:login')

@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {'user': request.user})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})

class CustomPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'accounts/change_password.html'
    success_url = reverse_lazy('accounts:profile')
    
    def form_valid(self, form):
        messages.success(self.request, 'Your password has been changed successfully!')
        return super().form_valid(form)

@login_required
def admin_users(request):
    if not request.user.is_admin_user():
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    users = User.objects.all().order_by('-created_at')
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'accounts/admin_users.html', {'page_obj': page_obj})

@login_required
def admin_edit_user(request, user_id):
    if not request.user.is_admin_user():
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.username} has been updated successfully!')
            return redirect('accounts:admin_users')
    else:
        form = AdminUserEditForm(instance=user)
    
    return render(request, 'accounts/admin_edit_user.html', {'form': form, 'user': user})

@login_required
def admin_delete_user(request, user_id):
    if not request.user.is_admin_user():
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, f'User {user.username} has been deleted successfully!')
        return redirect('accounts:admin_users')
    
    return render(request, 'accounts/admin_delete_user.html', {'user': user})