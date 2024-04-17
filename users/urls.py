from django.contrib.auth.views import LogoutView
from django.urls import path, include
from . import views

urlpatterns = [

    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('home/', views.home, name='home'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('social/signup/', views.signup_redirect, name='signup_redirect'),


]
