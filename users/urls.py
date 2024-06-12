from django.contrib.auth import views as auth_views
from django.urls import path, include
# from django_email_verification import urls as email_urls  # include the urls

from . import views

urlpatterns = [

    path('home/', views.home, name='home'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('', views.CustomLoginView.as_view(), name='login'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('delete/', views.delete_account, name='delete'),
    path('edit/', views.edit_profile_view, name='edit'),
    # path('email/', include(email_urls)),
    path('password-reset-confirm/<uidb64>/<token>/',
         views.CustomPasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'),
         name='password_reset_complete'),
    path('forgot/', views.ResetPasswordView.as_view(), name='forgot_pd'),
    path('social/signup/', views.signup_redirect, name='signup_redirect'),
    path("admin_dashboard/", views.AdminDashboardView.as_view(), name="admin_dashboard"),
    path("show_users/", views.ShowUsersView.as_view(), name="show_users"),
    path("edit_user/<int:pk>/", views.EditUserView.as_view(), name="edit_user"),
    path("delete_user/<int:pk>/", views.DeleteUserAdminView.as_view(), name="delete_user"),


]
