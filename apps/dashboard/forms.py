from django import forms
from django.contrib.auth import authenticate
from django.forms import ModelForm
from django.shortcuts import get_object_or_404
from .models import BatchSession
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit


class BatchSessionForm(forms.ModelForm):
    BEAN_TYPE_CHOICES = [
        ('robusta', 'Robusta'),
        ('liberica', 'Liberica'),
        ('excelsa', 'Excelsa'),
    ]

    title = forms.CharField(max_length=255, widget=forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),)
    bean_type = forms.ChoiceField(choices=BEAN_TYPE_CHOICES, widget=forms.Select(attrs={
                'class': 'form-control container-fluid',
            }))
    farm = forms.CharField(max_length=255)

    class Meta:
        model = BatchSession
        fields = ['title', 'bean_type', 'farm']
        
        
class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=255, required=False)
    last_name = forms.CharField(max_length=255, required=False)
    email = forms.CharField(widget=forms.EmailInput(), required=False)
    password = forms.CharField(widget=forms.PasswordInput(), required=False)
    reenter_password = forms.CharField(widget=forms.PasswordInput(), required=False)
    
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "password", "reenter_password"]
    
    # def save(self, commit=True):
    #     user_instance = get_object_or_404(User, id=sel)
    #     user_instance.first_name = self.cleaned_data['first_name']
    #     user_instance.last_name = self.cleaned_data['last_name']
    #     user_instance.email = self.cleaned_data['email']
        
        
    #     if commit:
    #         user_instance.save()
    #     return user_instance
    
    