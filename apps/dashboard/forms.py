from django import forms
from django.contrib.auth import authenticate
from django.forms import ModelForm
from .models import BatchSession

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