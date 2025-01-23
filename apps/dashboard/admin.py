from django.contrib import admin
from .models import BatchSession, DefectsDetected

admin.site.register(BatchSession)
admin.site.register(DefectsDetected)