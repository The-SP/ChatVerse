from django.db import models
from django.utils import timezone    
from django.contrib.auth.models import User  

class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    message = models.CharField(max_length=256)
    date = models.DateTimeField(default=timezone.localtime)

    def __str__(self):
        return self.message