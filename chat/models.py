from django.db import models
from django.utils import timezone    
from django.contrib.auth.models import User  

class Room(models.Model):
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    message = models.TextField()
    date = models.DateTimeField(default=timezone.localtime)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return self.message