import threading

from django.conf import settings
from django.core.mail import send_mail


def send_entity_init_email(user, password):
    def run():
        subject = "🆕 Compte super utilisateur CR-PAY créé"
        message = f"""
✅ Compte super utilisateur créé :

👤 Nom complet : {user.first_name} {user.last_name}
📧 Email       : {user.email}
📱 Téléphone   : {user.entity.phone if user.entity else 'N/A'}
🏷️  Code       : {user.entity.code if user.entity else 'N/A'}
🔐 Mot de passe : {password}
🆔 ID Entité   : {user.entity.entity_id if user.entity else 'N/A'}

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
