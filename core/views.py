from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, get_user_model, logout
from core.forms import LoginForm, SignupForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from questions.models import Profile
from django.db.models import Count
from django.utils.http import url_has_allowed_host_and_scheme

User = get_user_model()

@login_required(login_url=reverse_lazy("core:login"))
def profile(request, nickname=None):
    if nickname:
        profile = get_object_or_404(Profile.objects.select_related('user'), nickname=nickname)
        user = profile.user
        is_own_profile = False
        if request.user.is_authenticated and user == request.user:
            is_own_profile = True
    else:
        if not request.user.is_authenticated:
            return redirect('core:login')
        user = request.user
        profile, _ = Profile.objects.get_or_create(user=user)
        is_own_profile = True
    
    questions = user.questions.select_related('author').prefetch_related('tags').annotate(
        answers_count=Count('answers'), likes_count=Count('likes')).order_by('-created_at')
    answers = user.answers.select_related('question', 'author').order_by('-created_at')
    
    context = {"profile_user": user, "profile": profile, "questions": questions, "answers": answers, "is_own_profile": is_own_profile}
    return render(request, 'core/profile.html', context)


def user_login(request):
    next_url = request.GET.get("next")
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            login(request, user)
            
            if not form.cleaned_data.get("remember"):
                request.session.set_expiry(0)
            
            if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()},
                                                            require_https=request.is_secure()):
                return redirect(next_url)
            return redirect("questions:index")
    else:
        form = LoginForm()
    return render(request, "core/login.html", context={"form": form, "next": next_url})


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('questions:index')
    else:
        form = SignupForm()
    return render(request, 'core/signup.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('questions:index')
