from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import UserActivity

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            # Create UserActivity record for new user
            UserActivity.objects.create(user=user)
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Update last login and set logged in status
            user_activity = UserActivity.objects.get(user=user)
            user_activity.last_login = timezone.now()
            user_activity.is_logged_in = True
            user_activity.save()
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'register.html')

@login_required(login_url='register')
def home(request):
    return render(request, 'home.html')

def logout_view(request):
    if request.user.is_authenticated:
        # Update logout time and set logged in status to False
        user_activity = UserActivity.objects.get(user=request.user)
        user_activity.last_logout = timezone.now()
        user_activity.is_logged_in = False
        user_activity.save()
    logout(request)
    return redirect('register')
