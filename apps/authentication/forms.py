from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.forms import ModelForm
from django.shortcuts import get_object_or_404


class UserLoginForm(forms.Form):
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
    
class UserCreationForm(forms.Form):
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'required': True
    }))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'required': True
    }))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'required': True
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'required': True
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'required': True    
    }))

    def save(self, commit=True):
        user = User.objects.create_user(
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password']
        )
        if commit:
            user.save()
        return user


    
# class UserCreationForm(forms.ModelForm):
#     class Meta:
#         model = User
#         fields = ["first_name", "last_name", "username", "email", "password"]
#         widgets = {
#             'first_name': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'required': True
#             }),
#             'last_name': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'required': True
#             }),
#             'username': forms.TextInput(attrs={
#                 'class': 'form-control',
#             }),
#             'email': forms.EmailInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Enter your email',
#             }),
#             'password': forms.PasswordInput(attrs={
#                 'class': 'form-control',
#                 'required': True
#             }),
#         }

