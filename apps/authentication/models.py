from django.db import models

class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    fname = models.CharField(max_length=255, null=False)
    lname = models.CharField(max_length=255, null=False)
    email = models.CharField(max_length=255, null=False, unique=True)
    username = models.CharField(max_length=255, null=False, unique=True)
    password = models.CharField(max_length=255, null=False)
    
    
    def __str__(self):
        return f'User("{self.id}", "{self.fname}"'
    
