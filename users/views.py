from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import UserRegisterForm
from django.views.generic.edit import CreateView


# from django.contrib.auth.forms import UserCreationForm

class CustomLoginView(LoginView, SuccessMessageMixin):
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('home')
    success_message = "You were successfully logged in"

    def get_redirect_url(self):
        return self.success_url


class SignUpView(SuccessMessageMixin, CreateView):
    template_name = 'users/signup.html'
    success_url = reverse_lazy('login')
    form_class = UserRegisterForm
    success_message = "Your profile was created successfully"


def home(request):
    return render(request, 'home.html', {'user': request.user})


def signup_redirect(request):
    messages.error(request, "Something wrong here, it may be that you already have account!")
    return redirect("homepage")
