from django.contrib import admin
from .models import UserProfile, ChatMessage, MentalHealthReport

admin.site.register(UserProfile)
admin.site.register(ChatMessage)
admin.site.register(MentalHealthReport)