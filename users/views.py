from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

from .forms import EditUserForm, EditProfileForm
from .forms import SignInForm, SignUpForm
from .models import Profile
from django_email_verification import send_email


# from django.contrib.auth.forms import UserCreationForm

class CustomLoginView(LoginView, SuccessMessageMixin):
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('home')
    success_message = "You were successfully logged in"
    form_class = SignInForm

    def get_redirect_url(self):
        return self.success_url


class SignUpView(SuccessMessageMixin, CreateView):
    template_name = 'users/signup.html'
    success_url = reverse_lazy('home')
    form_class = SignUpForm
    success_message = "Your profile was created successfully"



class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')


def home(request):
    return render(request, 'header.html', {'user': request.user, "profile": Profile.objects.get(user=request.user)})


def signup_redirect(request):
    messages.error(request, "Something wrong here, it may be that you already have account!")
    return redirect("homepage")


@login_required
def edit_profile_view(request):
    profile = Profile.objects.get(user=request.user)
    user_form = EditUserForm(request.POST or None, instance=request.user)
    profile_form = EditProfileForm(request.POST or None, request.FILES or None,
                                   instance=Profile.objects.get(user=request.user))

    if request.method == 'POST':
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect(reverse_lazy('home'))

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
    }

    return render(request, 'users/edit.html', context)
