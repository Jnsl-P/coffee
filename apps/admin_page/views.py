from django.http import Http404
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic.list import ListView
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from .forms import AdminLoginForm
from django.views.generic.edit import DeleteView, UpdateView
from django.views.generic.detail import DetailView



class AdminLoginView(FormView):
    template_name = "admin_page/AdminLogin.html"
    form_class = AdminLoginForm
    success_url = reverse_lazy('admin_dashboard')

    def form_valid(self, form):
        user = form.user  # Retrieve the authenticated user
        if user.is_superuser:  # Check if the user is an admin
            login(self.request, user)  # Log in the user
            messages.add_message(self.request, messages.INFO, "Login Successfully")
        else:
            messages.add_message(self.request, messages.WARNING, "Invalid credentials")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.add_message(self.request, messages.WARNING, "Invalid credentials")
        return super().form_invalid(form)
        
    def get(self, request, *args, **kwargs):
        # Redirect authenticated users to the appropriate page
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return redirect(reverse_lazy('admin_dashboard'))
            else:
                return redirect(reverse_lazy('home'))
        return super().get(request, *args, **kwargs)
    
    
class AdminListView(LoginRequiredMixin, TemplateView):
    template_name = "admin_page/AdminListView.html"
    model = User
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["objects"] = User.objects.filter(is_superuser=0)
        return context
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        user = self.request.user
        if not user.is_superuser:
            return redirect(reverse_lazy('login'))
        
        return self.render_to_response(context)
    
class Admin_UserDetailView(LoginRequiredMixin, UpdateView):
    template_name = "admin_page/AdminUserView.html"
    success_url = reverse_lazy("admin_dashboard")
    fields = ["first_name", "last_name","email",]
    model = User

class DeleteUserView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = "admin_page/partials/DeleteUserView.html"
    success_url = reverse_lazy('admin_dashboard')

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        if user.is_superuser:
            messages.add_message(self.request, messages.WARNING, "Cannot delete a superuser")
            return redirect('admin_dashboard')
        messages.add_message(self.request, messages.INFO, "User deleted successfully")
        return super().delete(request, *args, **kwargs)