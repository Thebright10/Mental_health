from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings

from .models import UserProfile, ChatMessage, MentalHealthReport

import json
import joblib
import os
import requests


# ================= OPENROUTER =================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def openrouter_ai_response(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/llama-3-8b-instruct",
        "messages": [
            {"role": "system", "content": "You are a compassionate AI mental health support assistant."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        print("OpenRouter error:", response.text)
        return None
    except Exception as e:
        print("OpenRouter request error:", e)
        return None


# ================= HOME =================
def home(request):
    reports = []
    if request.user.is_authenticated:
        reports = MentalHealthReport.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "home.html", {"reports": reports})


# ================= STATIC PAGES =================
def about(request):
    return render(request, "about.html")

def reviews(request):
    return render(request, "reviews.html")

def partners(request):
    return render(request, "partners.html")

def chat_page(request):
    return render(request, "chatbot/chat.html")


# ================= AUTH SYSTEM =================
def register_view(request):
    if request.method == "POST":
        username  = request.POST.get("username", "").strip()
        email     = request.POST.get("email", "").strip()
        password  = request.POST.get("password", "")
        age       = request.POST.get("age")
        gender    = request.POST.get("gender", "").strip()
        family_email = request.POST.get("family_email", "").strip()
        family_phone = request.POST.get("family_phone", "").strip()
        carrier_gateway = request.POST.get("carrier_gateway", "airtelmail.com").strip()

        if User.objects.filter(username=username).exists():
            return render(request, "register.html", {"error": "Username already exists"})

        user = User.objects.create_user(username=username, email=email, password=password)

        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                "age": age if age else None,
                "gender": gender,
                "family_email": family_email or email,
                "family_phone": family_phone or "",
                "carrier_gateway": carrier_gateway,
            }
        )

        if not created:
            profile.age = age if age else None
            profile.gender = gender
            profile.family_email = family_email or email
            profile.family_phone = family_phone or ""
            profile.carrier_gateway = carrier_gateway
            profile.save()

        login(request, user)
        return redirect("home")

    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        return render(request, "login.html", {"error": "Wrong username or password"})
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("home")


def profile_view(request):
    if not request.user.is_authenticated:
        return redirect("login")

    profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "family_email": request.user.email or "",
            "family_phone": "",
            "gender": "",
            "carrier_gateway": "airtelmail.com",
        }
    )

    reports = MentalHealthReport.objects.filter(user=request.user).order_by("-created_at")
    chats   = ChatMessage.objects.filter(user=request.user).order_by("-created_at")[:10]

    return render(request, "profile.html", {
        "profile": profile,
        "reports": reports,
        "chats": chats
    })


# ================= EMOTION MODEL =================
emotion_labels = [
    "admiration","amusement","anger","annoyance","approval","caring",
    "confusion","curiosity","desire","disappointment","disapproval",
    "disgust","embarrassment","excitement","fear","gratitude",
    "grief","joy","love","nervousness","optimism","pride",
    "realization","relief","remorse","sadness","surprise","neutral"
]

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model/emotion_model.pkl")
model = joblib.load(MODEL_PATH)


@csrf_exempt
def detect_emotion(request):
    if request.method == "POST":
        text = request.POST.get("text", "hello")
        emotion_index = int(model.predict([text])[0])
        emotion = emotion_labels[emotion_index]
        return JsonResponse({"emotion": emotion})
    return JsonResponse({"emotion": "neutral"})


# ================= INTENT =================
def detect_intent(text):
    text = text.lower()
    if "joke" in text:
        return "joke"
    elif "movie" in text or "movies" in text:
        return "movie"
    elif "game" in text or "play" in text:
        return "game"
    elif "sad" in text or "stress" in text or "depressed" in text or "anxiety" in text:
        return "mental_health"
    else:
        return "general"


# ================= SUICIDE DETECTION =================
suicide_words = [
    "suicide", "kill myself", "die", "end my life",
    "no reason to live", "want to die", "self harm"
]


# ================= SCORE =================
def mental_health_score(text_emotion, face_emotion, text):
    score = 0
    negative      = ["sadness", "anger", "fear", "grief", "remorse", "nervousness"]
    positive_face = ["happy", "surprised"]

    if text_emotion in negative:
        score += 3
    if face_emotion in negative:
        score += 3

    text_lower = text.lower()
    for word in suicide_words:
        if word in text_lower:
            score += 10
            if face_emotion in positive_face:
                score -= 2

    return max(score, 0)


# ================= DECISION =================
def decision_engine(intent, text_emotion, face_emotion, score):
    if score >= 10:
        return "crisis_support"
    if intent == "joke":
        return "tell_joke"
    if intent == "movie":
        return "recommend_movie"
    if intent == "game":
        return "play_game"
    if intent == "mental_health":
        return "emotional_support"
    if text_emotion in ["sadness", "grief", "fear", "remorse"]:
        return "comfort_user"
    if text_emotion == "joy":
        return "casual_chat"
    return "general_chat"


# ================= AI RESPONSE =================
def generate_ai_response(action, user_message, text_emotion, face_emotion):
    prompt = f"""
You are an intelligent AI mental health assistant.

User message: {user_message}
Emotion (text): {text_emotion}
Emotion (face): {face_emotion}
Action: {action}

Instructions:
- Reply like a real human (not robotic)
- Keep response short (2–4 lines)
- Be emotionally aware
- Add suggestions when needed:

If user is sad:
→ suggest music, meditation, or talking to someone

If user misses someone:
→ suggest emotional songs

If user asks for songs:
→ suggest songs + YouTube link

If user asks for movies:
→ suggest 3 movies

If user asks for joke:
→ tell a funny joke

If serious mental distress:
→ give support + grounding advice

Do not repeat same sentences.
"""
    return openrouter_ai_response(prompt)


# ================= REPORT =================
def generate_report(user):
    chats = ChatMessage.objects.filter(user=user)
    if not chats.exists():
        return None

    avg_score = sum(chat.score for chat in chats) / chats.count()

    if avg_score >= 8:
        risk    = "HIGH"
        summary = "User showed strong signs of emotional distress and may require urgent support."
    elif avg_score >= 4:
        risk    = "MEDIUM"
        summary = "User showed moderate emotional stress and may benefit from monitoring and support."
    else:
        risk    = "LOW"
        summary = "User interaction suggests low immediate mental health risk at this time."

    return MentalHealthReport.objects.create(
        user=user,
        avg_score=avg_score,
        risk_level=risk,
        summary=summary
    )


# ================= ALERT: EMAIL =================
def send_alert_email(to_email, score, username="User"):
    """
    Sends a rich HTML email alert to the family member.
    Requires Django SMTP settings in settings.py:

        EMAIL_BACKEND    = 'django.core.mail.backends.smtp.EmailBackend'
        EMAIL_HOST       = 'smtp.gmail.com'
        EMAIL_PORT       = 587
        EMAIL_USE_TLS    = True
        EMAIL_HOST_USER  = 'adaksudip956@gmail.com'
        EMAIL_HOST_PASSWORD = 'zisb flua qing arsg'   # Gmail App Password
        DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
    """
    subject = "⚠️ MindfulAI Alert – Immediate Attention Needed"

    plain_message = f"""
Dear Family Member,

This is an automated alert from MindfulAI Companion.

User     : {username}
Risk Score: {score} / 15
Status   : HIGH RISK ⚠️

The system has detected signs of significant emotional distress during a recent chat session.
Please check on them as soon as possible.

Steps you can take:
  1. Call or message them right now.
  2. Stay with them if possible.
  3. Contact a crisis helpline if needed:
       iCall (India): 9152987821
       Vandrevala Foundation: 1860-2662-345

This is an automated message. Do not reply.

— MindfulAI Companion Team
"""

    html_message = f"""
<html>
<body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:30px;">
  <div style="max-width:540px;margin:auto;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1);">
    <div style="background:#7c3aed;padding:24px 30px;">
      <h1 style="color:#fff;margin:0;font-size:22px;">🧠 MindfulAI Companion</h1>
      <p style="color:#ddd6fe;margin:6px 0 0;font-size:13px;">Mental Health Monitoring Alert</p>
    </div>
    <div style="padding:28px 30px;">
      <div style="background:#fef2f2;border-left:4px solid #ef4444;padding:14px 18px;border-radius:6px;margin-bottom:22px;">
        <p style="margin:0;font-size:15px;font-weight:bold;color:#b91c1c;">⚠️ High Risk Detected</p>
        <p style="margin:6px 0 0;color:#dc2626;font-size:13px;">Immediate attention may be required.</p>
      </div>
      <table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:22px;">
        <tr style="border-bottom:1px solid #e5e7eb;">
          <td style="padding:10px 0;color:#6b7280;width:40%;">User</td>
          <td style="padding:10px 0;font-weight:600;color:#111827;">{username}</td>
        </tr>
        <tr style="border-bottom:1px solid #e5e7eb;">
          <td style="padding:10px 0;color:#6b7280;">Risk Score</td>
          <td style="padding:10px 0;font-weight:600;color:#dc2626;">{score} / 15</td>
        </tr>
        <tr>
          <td style="padding:10px 0;color:#6b7280;">Status</td>
          <td style="padding:10px 0;">
            <span style="background:#fee2e2;color:#b91c1c;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;">HIGH RISK</span>
          </td>
        </tr>
      </table>
      <p style="font-size:14px;color:#374151;margin-bottom:16px;"><strong>Recommended steps:</strong></p>
      <ol style="font-size:14px;color:#374151;padding-left:18px;line-height:1.8;">
        <li>Call or message <strong>{username}</strong> immediately.</li>
        <li>Stay with them if possible.</li>
        <li>Contact a crisis helpline if needed:<br/>
          <span style="color:#7c3aed;">iCall (India): <strong>9152987821</strong></span><br/>
          <span style="color:#7c3aed;">Vandrevala Foundation: <strong>1860-2662-345</strong></span>
        </li>
      </ol>
    </div>
    <div style="background:#f9fafb;padding:16px 30px;text-align:center;font-size:12px;color:#9ca3af;">
      This is an automated alert from MindfulAI Companion. Do not reply to this email.
    </div>
  </div>
</body>
</html>
"""

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"✅ Alert email sent to {to_email}")
    except Exception as e:
        print(f"❌ Email alert failed: {e}")


# ================= ALERT: SMS VIA EMAIL GATEWAY (FREE) =================
def send_alert_sms_via_gateway(phone_number, carrier_gateway, score, username="User"):
    """
    Sends a FREE SMS using email-to-SMS gateway. No Twilio needed.

    Common Indian gateways:
        Airtel  →  airtelmail.com
    Common US gateways:
        AT&T    →  txt.att.net
        T-Mobile→  tmomail.net
        Verizon →  vtext.com

    Store the user's carrier_gateway in UserProfile.
    Example SMS address: 9876543210@airtelmail.com
    """
    sms_address = f"{phone_number}@{carrier_gateway}"
    subject = "MindfulAI Alert"
    message = (
        f"URGENT: {username} may need help. "
        f"Risk score: {score}/15. "
        f"Please call them now. "
        f"iCall: 9152987821"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[sms_address],
            fail_silently=False,
        )
        print(f"✅ SMS alert sent to {sms_address}")
    except Exception as e:
        print(f"❌ SMS via gateway failed: {e}")


# ================= ALERT: SMS VIA FAST2SMS API (India — Free Tier) =================
def send_alert_sms_fast2sms(phone_number, score, username="User"):
    """
    Sends SMS via Fast2SMS free API (India only).
    Sign up at https://fast2sms.com → get free API key → 100 SMS/day free.

    Add to settings.py:
        FAST2SMS_API_KEY = 'your_fast2sms_api_key'
    """
    api_key = getattr(settings, "FAST2SMS_API_KEY", None)
    if not api_key:
        print("❌ FAST2SMS_API_KEY not set in settings.py")
        return

    message = (
        f"MindfulAI ALERT: {username} needs immediate help. "
        f"Risk score: {score}/15. Please call them now. "
        f"iCall helpline: 9152987821"
    )

    url = "https://www.fast2sms.com/dev/bulkV2"
    headers = {"authorization": api_key}
    payload = {
        "route": "q",
        "message": message,
        "language": "english",
        "flash": 0,
        "numbers": phone_number,
    }

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        result = response.json()
        if result.get("return"):
            print(f"✅ Fast2SMS alert sent to {phone_number}")
        else:
            print(f"❌ Fast2SMS error: {result}")
    except Exception as e:
        print(f"❌ Fast2SMS request failed: {e}")


# ================= UNIFIED ALERT DISPATCHER =================
def send_all_alerts(profile, score, username):
    """
    Dispatches all available alert channels:
      1. Rich HTML email  → family_email
      2. SMS via gateway  → family_phone + carrier_gateway
      3. SMS via Fast2SMS → family_phone (India, free tier)
    """
    # 1. Email alert
    if profile.family_email:
        send_alert_email(profile.family_email, score, username)

    # 2. SMS via email-to-SMS gateway
    if profile.family_phone:
        carrier = getattr(profile, "carrier_gateway", "airtelmail.com") or "airtelmail.com"
        send_alert_sms_via_gateway(profile.family_phone, carrier, score, username)

    # 3. SMS via Fast2SMS (India — uncomment if you have API key)
    # if profile.family_phone:
    #     send_alert_sms_fast2sms(profile.family_phone, score, username)


# ================= CHAT =================
@csrf_exempt
def chat(request):
    if request.method != "POST":
        return JsonResponse({"reply": "Invalid request"})

    if not request.user.is_authenticated:
        return JsonResponse({"reply": "Please login first."})

    try:
        data         = json.loads(request.body)
        message      = data.get("message", "").strip()
        face_emotion = data.get("emotion", "neutral")

        if not message:
            return JsonResponse({"reply": "Please type something."})

        text_emotion_index = int(model.predict([message])[0])
        text_emotion       = emotion_labels[text_emotion_index]

        intent = detect_intent(message)
        score  = mental_health_score(text_emotion, face_emotion, message)
        action = decision_engine(intent, text_emotion, face_emotion, score)

        if score >= 5:
            reply = (
                "I'm really sorry you're feeling this way. You matter, and you do not have to "
                "handle this alone. Please contact someone you trust right now, stay near another "
                "person if possible, and reach out to a local emergency or crisis helpline."
            )
        else:
            reply = generate_ai_response(action, message, text_emotion, face_emotion)

        ChatMessage.objects.create(
            user=request.user,
            message=message,
            reply=reply,
            text_emotion=text_emotion,
            face_emotion=face_emotion,
            score=score
        )

        end_chat = False

        if score >= 7:
            report = generate_report(request.user)

            profile, _ = UserProfile.objects.get_or_create(
                user=request.user,
                defaults={
                    "family_email": request.user.email or "",
                    "family_phone": "",
                    "gender": "",
                    "carrier_gateway": "airtelmail.com",
                }
            )

            # Fire all alert channels
            send_all_alerts(profile, score, request.user.username)

            end_chat = True

        return JsonResponse({
            "reply": reply,
            "text_emotion": text_emotion,
            "face_emotion": face_emotion,
            "score": score,
            "end_chat": end_chat
        })

    except Exception as e:
        print("Chat error:", e)
        return JsonResponse({"reply": "Something went wrong. Please try again."})


# ================= END CHAT =================
@csrf_exempt
def end_chat(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({"status": "error", "message": "Please login first"})

        report = generate_report(request.user)

        if report:
            return JsonResponse({"status": "success", "report": report.summary})

        return JsonResponse({"status": "success", "report": "No chat history found."})

    return JsonResponse({"status": "error", "message": "Invalid request"})


# ================= EXTRA PAGES =================
def crisis_help(request):
    return render(request, 'crisis_help.html')

def accessibility(request):
    return render(request, 'accessibility.html')

def cookie_policy(request):
    return render(request, 'cookie_policy.html')

def terms_of_use(request):
    return render(request, 'terms_of_use.html')

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def community(request):
    return render(request, 'community.html')

def meditation_guide(request):
    return render(request, 'meditation_guide.html')

def therapy_tips(request):
    return render(request, 'therapy_tips.html')