from itsdangerous import URLSafeTimedSerializer
from django.conf import settings
import requests

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
    verify_url = f"http://127.0.0.1:8000/api/auth/verify-email/?token={token}"

    mailtrap_url = "https://sandbox.api.mailtrap.io/api/send/3629848"
    payload = {
        "from": {
            "email": "ilseromero35@gmail.com",
            "name": "Sistema SPOS"
        },
        "to": [
            {
                "email": user.email
            }
        ],
        "subject": "Verifica tu cuenta",
        "text": f"Hola {user.name},\n\nGracias por registrarte en nuestro sistema.\nPor favor haz clic en el siguiente enlace para verificar tu correo:\n{verify_url}\n\nSi no solicitaste esta cuenta, puedes ignorar este mensaje.",
        "category": "Verificación"
    }

    headers = {
        "Authorization": "Bearer 3d3d6ac5d740c67805e96925bb495e58",  # ¡Pon tu token seguro en .env!
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(mailtrap_url, json=payload, headers=headers)
        response.raise_for_status()
        print(verify_url)
        print("✅ Correo de verificación enviado a", user.email)
    except requests.exceptions.RequestException as e:
        print("❌ Error al enviar correo:", e)
