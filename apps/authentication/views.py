from django.shortcuts import render,redirect
from django.views.generic import TemplateView
from django.views.generic.edit import FormView, View, CreateView
from django.views.generic.list import ListView
from django.contrib.auth import authenticate, login,logout
from .forms import UserLoginForm, UserCreationForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.models import User
from django import forms


class loginView(FormView):
    template_name = "auth/login.html"
    form_class = UserLoginForm
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        user = form.user  # Retrieve the authenticated user
        if user.username != "admin" and user.password != "admin":    
            login(self.request, user)  # Log in the user
            messages.add_message(self.request, messages.INFO, "Login Successful")
        else:
            messages.add_message(self.request, messages.WARNING, "Invalid credentials")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.add_message(self.request, messages.WARNING, form.error)
        return super().form_invalid(form)
        
    def get(self, request, *args, **kwargs):
        # Redirect authenticated users to the home page
        if request.user.is_authenticated:
            if request.user.username == "admin":
                return redirect(reverse_lazy('admin_dashboard'))
            else:
                return redirect(self.success_url)
        return super().get(request, *args, **kwargs)
    
class UserCreateView(FormView):
    template_name = "auth/user_form.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    
    def form_valid(self, form):
        if form.cleaned_data.get("password") == form.cleaned_data.get("password2"):
            form.save()
        else:
            messages.add_message(self.request, messages.WARNING, "Password did not match!")
            self.success_url = reverse_lazy('register')
            
        if form.cleaned_data.get("password"):
            form.save()
        else:
            messages.add_message(self.request, messages.WARNING, "Password did not match!")
            self.success_url = reverse_lazy('register')
            
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.WARNING, form.error)
        return super().form_invalid(form)
    

def logout_user(request):
    print("USER:", request.user)
    logout(request)
    return redirect("index")
