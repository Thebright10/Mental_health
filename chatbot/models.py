from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    family_email = models.EmailField()
    family_phone = models.CharField(max_length=15)

    def __str__(self):
        return self.user.username


class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    reply = models.TextField()
    text_emotion = models.CharField(max_length=50)
    face_emotion = models.CharField(max_length=50)
    score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class MentalHealthReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    avg_score = models.FloatField()
    risk_level = models.CharField(max_length=20)
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    




@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)