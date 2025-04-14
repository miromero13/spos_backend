from itsdangerous import URLSafeTimedSerializer
from django.conf import settings

def generate_token(email):
    s = URLSafeTimedSerializer(settings.SECRET_KEY)
    return s.dumps(email, salt='email-confirm')

def verify_token(token, max_age=3600):
    s = URLSafeTimedSerializer(settings.SECRET_KEY)
    try:
        return s.loads(token, salt='email-confirm', max_age=max_age)
    except Exception:
        return None

def send_verification_email(user):
    token = generate_token(user.email)
    url = f"http://127.0.0.1:8000/api/auth/verify_email/?token={token}"
    print(f"🔗 Link de verificación para {user.email}: {url}")
