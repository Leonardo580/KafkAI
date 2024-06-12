import json
from django.core.paginator import Paginator

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetConfirmView
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from .forms import EditUserForm, EditProfileForm, CustomPasswordResetForm, CustomSetPasswordForm, EditUserAdminForm, \
    AddUserForm
from .forms import SignInForm, SignUpForm
from .models import Profile
from django.contrib import messages


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
    is_chats_low = len(chats) < 10
    return render(request, 'header.html',
                  {'user': request.user, "profile": Profile.objects.get(user=request.user), "chats": chats,
                   "isChats": not is_chats_low})


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


#### ADMIN DASHBOARD ####


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.warning(self.request, "You don't have permission to access this page")
        return redirect('home')


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'admin.html'


class ShowUsersView(AdminRequiredMixin, TemplateView):
    template_name = 'users/admin/show.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Retrieve all users
        users = User.objects.all().order_by('username')

        # Paginate the users
        paginator = Paginator(users, 20)  # Show 10 users per page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['users'] = page_obj
        context['edit_user_form'] = EditUserForm()
        context['add_user_form'] = AddUserForm()
        return context

    def post(self, request, *args, **kwargs):
        form = AddUserForm(request.POST)
        if form.is_valid():
            # Handle AddUserForm submission
            user = form.save()
            # Perform any additional actions, such as sending a welcome email or setting up the user's profile
            return redirect(reverse_lazy('show_users'))

        # If the form is not valid, or if neither form was submitted, render the template with the existing context
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)


class EditUserView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    form_class = AddUserForm
    template_name = 'users/admin/edit_user.html'
    success_url = reverse_lazy('show_users')
    success_message = "User updated successfully"


class DeleteUserAdminView(AdminRequiredMixin, View):
    def get(self, request, pk):
        # Get the user object
        user = get_object_or_404(User, id=pk)
        # Delete the user
        if user == request.user:
            messages.error(request, "You can't delete yourself")
            return reverse_lazy('show_users')
        user.delete()

        # Redirect to the 'show_user' view
        return reverse_lazy('show_user')
