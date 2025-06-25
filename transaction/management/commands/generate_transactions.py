import random
from datetime import timedelta, datetime
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from transaction.models import Transaction, Entity  # adapte à ton app

class Command(BaseCommand):
    help = "Génère 10 000 transactions de test"

    def handle(self, *args, **options):
        entities = list(Entity.objects.all())
        if not entities:
            self.stdout.write(self.style.ERROR("Aucune entité trouvée. Créez-en d'abord."))
            return

        status_choices = ["PENDING", "SUCCESS", "FAILED"]
        purposes = [
            "Électricité", "Eau", "Internet", "Téléphonie mobile",
            "Télévision", "Autre", "Permis de conduire", "Assurance auto"
        ]
        now = datetime.now()
        transactions = []

        for i in range(1, 10001):
            entity = random.choice(entities)
            status = random.choice(status_choices)
            purpose = random.choice(purposes)
            amount = round(random.uniform(1000, 100000), 2)

            # Répartir les dates sur 60 jours
            days_ago = random.randint(0, 60)
            seconds_offset = random.randint(0, 86400)
            created_at = make_aware(now - timedelta(days=days_ago, seconds=seconds_offset))

            # Référence formatée
            date_part = created_at.strftime("%Y%m%d")
            reference = f"TX-{date_part}-{str(i).zfill(4)}"

            transaction = Transaction(
                reference=reference,
                entity=entity,
                details={"info": "Transaction de test générée"},
                purpose=purpose,
                amount=amount,
                status=status,
                created_at=created_at,
                updated_at=created_at
            )
            transactions.append(transaction)

            if i % 1000 == 0:
                self.stdout.write(f"{i} transactions préparées...")

        Transaction.objects.bulk_create(transactions, batch_size=1000)
        self.stdout.write(self.style.SUCCESS("✅ 10 000 transactions créées avec succès"))
