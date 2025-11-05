from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta

from entity.models import Entity
from transaction.models import Transaction, PaymentProviderLog


class Command(BaseCommand):
    help = 'Generate fake data for development - 1000 transactions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing transactions and logs before generating new data',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=5000,
            help='Number of transactions to generate (default: 5000)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            PaymentProviderLog.objects.all().delete()
            Transaction.objects.all().delete()
            # Ne pas supprimer les entités car elles peuvent avoir des utilisateurs
            self.stdout.write(self.style.SUCCESS('Existing transactions and logs cleared!'))
        
        self.stdout.write('Generating fake data...')
        
        # Créer des entités fake si elles n'existent pas
        entities = self.create_fake_entities()
        
        # Générer les transactions
        count = options.get('count', 5000)
        self.create_fake_transactions(entities, count)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully generated fake data!')
        )

    def create_fake_entities(self):
        """Créer des entités fake pour les tests"""
        entities_data = [
            {"code": "MERCHANT_001", "name": "Restaurant Le Gourmet", "entity_type": "MERCHANT", "country": "Burkina Faso"},
            {"code": "MERCHANT_002", "name": "Boutique Mode & Style", "entity_type": "MERCHANT", "country": "Côte d'Ivoire"},
            {"code": "MERCHANT_003", "name": "Pharmacie Centrale", "entity_type": "MERCHANT", "country": "Senegal"},
            {"code": "CLIENT_001", "name": "Orange Money API", "entity_type": "CLIENT", "country": "Mali"},
            {"code": "CLIENT_002", "name": "Wave Mobile Money", "entity_type": "CLIENT", "country": "Burkina Faso"},
            {"code": "MERCHANT_004", "name": "Station Shell Ouaga", "entity_type": "MERCHANT", "country": "Burkina Faso"},
            {"code": "MERCHANT_005", "name": "Supermarché Marina", "entity_type": "MERCHANT", "country": "Côte d'Ivoire"},
            {"code": "CLIENT_003", "name": "MTN Mobile Money", "entity_type": "CLIENT", "country": "Ghana"},
        ]
        
        entities = []
        for entity_data in entities_data:
            entity, created = Entity.objects.get_or_create(
                code=entity_data["code"],
                defaults={
                    "name": entity_data["name"],
                    "entity_type": entity_data["entity_type"],
                    "country": entity_data["country"],
                    "is_active": True,
                    "phone": f"+226{random.randint(10000000, 99999999)}"
                }
            )
            entities.append(entity)
            if created:
                self.stdout.write(f'Created entity: {entity.name}')
        
        return entities

    def create_fake_transactions(self, entities, count):
        """Générer des transactions fake"""
        statuses = ["PENDING", "SUCCESS", "FAILED"]
        # Pondération réaliste des statuts
        status_weights = [0.15, 0.75, 0.10]  # 15% PENDING, 75% SUCCESS, 10% FAILED
        
        purposes = [
            "Achat en ligne",
            "Paiement facture électricité",
            "Transfert d'argent",
            "Achat carburant",
            "Paiement restaurant",
            "Achat médicaments",
            "Recharge téléphone",
            "Paiement loyer",
            "Achat vêtements",
            "Paiement transport"
        ]
        
        transactions_created = 0
        
        # Date de base : il y a 3 mois (90 jours)
        base_date = timezone.now() - timedelta(days=90)
        
        for i in range(count):
            # Générer une date aléatoire sur les 3 derniers mois (0 à 90 jours depuis base_date)
            random_days = random.randint(0, 90)
            random_hours = random.randint(0, 23)
            random_minutes = random.randint(0, 59)
            
            created_date = base_date + timedelta(
                days=random_days, 
                hours=random_hours, 
                minutes=random_minutes
            )
            
            # Sélectionner un statut avec pondération
            status = random.choices(statuses, weights=status_weights)[0]
            
            # Créer la transaction
            transaction = Transaction.objects.create(
                reference=f"TXN{str(i+1).zfill(6)}_{random.randint(1000, 9999)}",
                entity=random.choice(entities),
                amount=Decimal(str(round(random.uniform(500, 50000), 2))),
                status=status,
                purpose=random.choice(purposes),
                details={
                    "sender_phone": f"+226{random.randint(10000000, 99999999)}",
                    "receiver_phone": f"+226{random.randint(10000000, 99999999)}",
                    "payment_method": random.choice(["ORANGE_MONEY", "WAVE", "CORIS_MONEY", "MOOV_MONEY"]),
                    "currency": "GNF",
                    "description": f"Paiement {random.choice(purposes).lower()}",
                    "merchant_code": f"MCH{random.randint(100, 999)}"
                },
                created_at=created_date,
                updated_at=created_date + timedelta(minutes=random.randint(1, 60))
            )
            
            # Forcer la date de création dans la base
            Transaction.objects.filter(uuid=transaction.uuid).update(
                created_at=created_date,
                updated_at=created_date + timedelta(minutes=random.randint(1, 60))
            )
            
            # Créer un log InTouch pour certaines transactions (70% de chance)
            if random.random() < 0.7:
                self.create_intouch_log(transaction, created_date)
            
            transactions_created += 1
            
            if transactions_created % 500 == 0:
                self.stdout.write(f'Created {transactions_created} transactions...')
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {transactions_created} transactions!')
        )

    def create_intouch_log(self, transaction, base_date):
        """Créer un log InTouch pour une transaction"""
        log_statuses = ["SENT", "RECEIVED", "SUCCESS", "FAILED"]
        
        # Date d'envoi légèrement après la création de la transaction
        sent_date = base_date + timedelta(minutes=random.randint(1, 5))
        
        # Date de callback (si applicable)
        callback_date = None
        if random.random() < 0.8:  # 80% de chance d'avoir un callback
            callback_date = sent_date + timedelta(minutes=random.randint(1, 30))
        
        PaymentProviderLog.objects.create(
            transaction=transaction,
            sent_at=sent_date,
            callback_received_at=callback_date,
            provider="MPP",
            request_payload={
                "amount": str(transaction.amount),
                "currency": "GNF",
                "reference": transaction.reference,
                "phone": transaction.details.get("sender_phone", ""),
                "description": transaction.purpose,
                "webhook_url": "https://staging.crdigital.tech/api/v0/payments/callback"
            },
            response_payload={
                "status": "success" if transaction.status == "SUCCESS" else "pending",
                "transaction_id": f"MPP{random.randint(100000, 999999)}",
                "reference": transaction.reference,
                "message": "Transaction initiated successfully"
            } if callback_date else None,
            http_status=200 if callback_date else None,
            status=random.choice(log_statuses)
        )