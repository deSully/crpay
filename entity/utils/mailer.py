import threading

from django.conf import settings
from django.core.mail import send_mail


def send_entity_init_email(user, password):
    def run():
        subject = "🆕 Compte super utilisateur CR-PAY créé"
        message = f"""
✅ Compte super utilisateur créé :

👤 Nom complet : {user.name}
📧 Email       : {user.email}
📱 Téléphone   : {user.phone}
🏷️  Code       : {user.code}
🔐 Mot de passe : {password}
🆔 ID Entité   : {user.entity_id}

Connectez-vous au système pour configurer les autres paramètres de sécurité.
        """.strip()

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_ADMIN_RECEIVER],
            fail_silently=False,
        )

    thread = threading.Thread(target=run)
    thread.start()
