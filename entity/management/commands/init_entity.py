# core/management/commands/init_entity.py

import random
import string

from django.core.management.base import BaseCommand

from entity.models import Entity
from entity.utils.mailer import send_entity_init_email


class Command(BaseCommand):
    help = "Initialise l'entité de base CR-PAY (type interne) avec un superuser"

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-email",
            action="store_true",
            help="Ne pas envoyer de mail après création",
        )

    def handle(self, *args, **options):
        if Entity.objects.filter(email="support@crdigital.tech").exists():
            self.stdout.write(self.style.WARNING("⚠️  L'entité existe déjà."))
            return

        password = "".join(random.choices(string.ascii_letters + string.digits, k=12))
        code = "CR" + "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )

        user = Entity.objects.create_superuser(
            username="crpay-admin",
            email="support@crdigital.tech",
            password=password,
            first_name="Retice sidney",
            last_name="ASSINONVO",
            name="~Retice sidney ASSINONVO",
            phone="+224610493839",
            entity_type="INTERNAL",
            code=code,
            country="Guinée",
        )

        self.stdout.write(self.style.SUCCESS("✅ Entité superuser créée avec succès"))
        self.stdout.write(f"📧 Email        : {user.email}")
        self.stdout.write(f"🔐 Mot de passe : {password}")
        self.stdout.write(f"🏷️  Code        : {code}")
        self.stdout.write(f"🆔 ID Entité    : {user.entity_id}")

        if not options["no_email"]:
            send_entity_init_email(user, password)
            self.stdout.write("📤 Email de confirmation envoyé.")
        else:
            self.stdout.write("📪 Email ignoré (--no-email)")
