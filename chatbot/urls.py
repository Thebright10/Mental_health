from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('reviews/', views.reviews, name='reviews'),
    path('partners/', views.partners, name='partners'),
    path('chat/', views.chat_page, name='chat_page'),

    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    path('chatbot/chat/', views.chat, name='chat_api'),
    path('detect-emotion/', views.detect_emotion, name='detect_emotion'),
    path('end-chat/', views.end_chat, name='end_chat'),
     # New pages
    path('crisis_help/', views.crisis_help, name='crisis_help'),
    path('accessibility/', views.accessibility, name='accessibility'),
    path('cookie_policy/', views.cookie_policy, name='cookie_policy'),
    path('terms_of_use/', views.terms_of_use, name='terms_of_use'),
    path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
    path('community/', views.community, name='community'),
    path('meditation_guide/', views.meditation_guide, name='meditation_guide'),
    path('therapy_tips/', views.therapy_tips, name='therapy_tips'),
]