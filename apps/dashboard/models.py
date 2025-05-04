from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now



# Create your models here.
class BatchSession(models.Model):
    batch_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, null=False)
    date_created = models.DateTimeField(default=now)
    bean_type = models.CharField(max_length=50)
    farm = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f'BatchSession("{self.batch_id}", "{self.title}")'
    
class DefectsDetected(models.Model):
    id = models.AutoField(primary_key=True)
    scan_number = models.IntegerField(null=False)
    date_scanned = models.DateTimeField(default=now)
    defects_detected = models.JSONField(max_length=50)
    scanned_image = models.CharField(max_length=255)
    scanned_image2 = models.CharField(max_length=255, null=True)
    batch = models.ForeignKey(BatchSession, on_delete=models.CASCADE)
    
    def __str__(self):
        return f'DefectsDetected("{self.id}", "{self.batch_id}")'