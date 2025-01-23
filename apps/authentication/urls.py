from django.contrib import admin
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('login/', views.loginView.as_view(), name="login"),
    path('register/', views.UserCreateView.as_view(), name="register"),
    path('logout/', views.logout_user, name="logout"),
]  
