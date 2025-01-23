from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth import authenticate


class AdminLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        user = authenticate(username=username, password=password)
        if not user:
            self.error = "Invalid Credentials"
            raise forms.ValidationError("Invalid username or password.")
        self.user = user  # Save the authenticated user
        return cleaned_data
    