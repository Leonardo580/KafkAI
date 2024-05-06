import json

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetConfirmView
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic.edit import CreateView

from .forms import EditUserForm, EditProfileForm, CustomPasswordResetForm, CustomSetPasswordForm
from .forms import SignInForm, SignUpForm
from .models import Profile


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
    success_url = reverse_lazy('login')
    form_class = SignUpForm
    success_message = "Your profile was created successfully"


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'users/password_reset.html'
    success_url = reverse_lazy('login')
    email_template_name = 'users/password_body.html'
    subject_template_name = 'users/password_body.txt'
    form_class = CustomPasswordResetForm


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    success_url = reverse_lazy('password_reset_complete')
    form_class = CustomSetPasswordForm


# def forgot_password(request):
#     pprint(vars(request))
#     if request.method == "POST":
#         username = request.POST["username"]
#         user = User.objects.get(username=username)
#         send_password(user, thread=True, expiry=None, context=None)
#         return render(request, 'users/check_email.html')
#     return redirect(reverse_lazy("login"))


@login_required
def home(request):
    chats = request.user.chats.all().order_by('-created_at')[:10]
    return render(request, 'header.html',
                  {'user': request.user, "profile": Profile.objects.get(user=request.user), "chats": chats})


def signup_redirect(request):
    messages.error(request, "Something wrong here, it may be that you already have account!")
    return redirect(reverse_lazy('home'))


@login_required
@require_POST
@csrf_exempt
def delete_account(request):
    try:
        request_data = json.loads(request.body.decode('utf-8'))
        user_id = request_data.get('userId')
        user = User.objects.get(id=user_id)
        user.delete()
        logout(request)
        return JsonResponse({'success': True})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
    # except Exception as e:
    #     return JsonResponse({'success': False, 'error': str(e)}, status=500)


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
