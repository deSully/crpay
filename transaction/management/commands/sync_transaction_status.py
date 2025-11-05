import asyncio
import httpx
import os
from django.core.management.base import BaseCommand
from django.core.cache import cache
from transaction.models import Transaction


class Command(BaseCommand):
    help = "Synchronise le statut des transactions PENDING avec MPP"

    def add_arguments(self, parser):
        parser.add_argument(
            '--transaction-id',
            type=str,
            help='UUID spécifique d\'une transaction à synchroniser'
        )
        parser.add_argument(
            '--max-age-hours',
            type=int,
            default=24,
            help='Synchroniser uniquement les transactions de moins de X heures (défaut: 24h)'
        )

    def handle(self, *args, **options):
        transaction_id = options.get('transaction_id')
        max_age_hours = options.get('max_age_hours')

        if transaction_id:
            # Sync une transaction spécifique
            try:
                transaction = Transaction.objects.get(uuid=transaction_id)
                self.stdout.write(f"Synchronisation de {transaction.reference}...")
                asyncio.run(self.sync_transaction(transaction))
            except Transaction.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Transaction {transaction_id} introuvable"))
        else:
            # Sync toutes les transactions PENDING récentes
            from django.utils import timezone
            from datetime import timedelta
            
            cutoff = timezone.now() - timedelta(hours=max_age_hours)
            pending_transactions = Transaction.objects.filter(
                status="PENDING",
                created_at__gte=cutoff
            )
            
            count = pending_transactions.count()
            self.stdout.write(f"🔄 {count} transaction(s) PENDING à synchroniser...")
            
            for transaction in pending_transactions:
                asyncio.run(self.sync_transaction(transaction))
            
            self.stdout.write(self.style.SUCCESS(f"✅ Synchronisation terminée: {count} transaction(s) vérifiée(s)"))

    async def sync_transaction(self, transaction):
        """
        Récupère le statut d'une transaction depuis MPP et met à jour
        """
        try:
            # 1. S'authentifier
            access_token = await self.get_access_token()
            
            # 2. Récupérer le statut depuis MPP
            base_url = os.getenv("MPP_BASE_URL", "https://gateway.mpp.bnbcash.app")
            url = f"{base_url}/api/v1/transaction/{transaction.reference}/get-status"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=30.0)
            
            if response.status_code == 200:
                data = response.json()
                mpp_status = data.get("data", {}).get("status", "unknown")
                
                # 3. Mapper le statut MPP vers notre statut
                new_status = self.map_mpp_status(mpp_status)
                
                if new_status != transaction.status:
                    old_status = transaction.status
                    transaction.status = new_status
                    transaction.save(update_fields=["status", "updated_at"])
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ {transaction.reference}: {old_status} → {new_status} (MPP: {mpp_status})"
                        )
                    )
                else:
                    self.stdout.write(f"   {transaction.reference}: Aucun changement ({transaction.status})")
            
            elif response.status_code == 404:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  {transaction.reference}: Transaction introuvable sur MPP")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ {transaction.reference}: Erreur HTTP {response.status_code}"
                    )
                )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ {transaction.reference}: Erreur - {str(e)}")
            )

    async def get_access_token(self):
        """
        Obtenir un token MPP (avec cache)
        """
        cache_key = "mpp_access_token"
        cached_token = cache.get(cache_key)
        if cached_token:
            return cached_token
        
        base_url = os.getenv("MPP_BASE_URL", "https://gateway.mpp.bnbcash.app")
        url = f"{base_url}/api/auth/token"
        payload = {
            "secret_id": os.environ["MPP_SECRET_ID"],
            "secret_key": os.environ["MPP_SECRET_KEY"]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=30.0)
            
            if response.status_code == 200:
                data = response.json()
                access_token = data["data"]["access_token"]
                cache.set(cache_key, access_token, 25 * 60)  # 25 minutes
                return access_token
            else:
                raise Exception(f"Authentication failed: {response.text}")

    def map_mpp_status(self, mpp_status):
        """
        Convertir le statut MPP en notre statut interne
        """
        status_mapping = {
            "initiated": "PENDING",
            "pending": "PENDING",
            "processing": "PENDING",
            "transmitted": "PENDING",
            "completed": "SUCCESS",
            "failed": "FAILED",
            "rejected": "FAILED",
            "cancelled": "FAILED",
        }
        return status_mapping.get(mpp_status.lower(), "PENDING")
