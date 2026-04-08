from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # CONNECT CHATBOT APP
    path('', include('chatbot.urls')),   # ✅ THIS IS VERY IMPORTANT
]