import json
import os
import urllib.request
import urllib.parse
import urllib.error

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
            default=72,
            help='Synchroniser uniquement les transactions de moins de X heures (défaut: 72h = 3 jours)'
        )

    def handle(self, *args, **options):
        transaction_id = options.get('transaction_id')
        max_age_hours = options.get('max_age_hours')

        if transaction_id:
            # Sync une transaction spécifique
            try:
                transaction = Transaction.objects.get(uuid=transaction_id)
                self.stdout.write(f"Synchronisation de {transaction.reference}...")
                self.sync_transaction(transaction)
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
                self.sync_transaction(transaction)
            
            self.stdout.write(self.style.SUCCESS(f"✅ Synchronisation terminée: {count} transaction(s) vérifiée(s)"))

    def sync_transaction(self, transaction):
        """
        Récupère le statut d'une transaction depuis MPP et met à jour
        """
        try:
            # 0. Vérifier qu'on a l'ID MPP
            details = transaction.details or {}
            mpp_transaction_id = details.get("mpp_transaction_id")
            
            if not mpp_transaction_id:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  {transaction.reference}: Pas d'ID MPP trouvé (transaction pas encore envoyée à MPP?)"
                    )
                )
                return
            
            # 1. S'authentifier
            access_token = self.get_access_token()
            
            # 2. Récupérer le statut depuis MPP
            base_url = os.getenv("MPP_BASE_URL", "https://gateway.mpp.bnbcash.app")
            url = f"{base_url}/api/v1/transaction/{mpp_transaction_id}/get-status"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # GET request avec urllib
            req = urllib.request.Request(url, headers=headers, method='GET')
            
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    response_data = json.loads(response.read().decode('utf-8'))
                    
                    mpp_status = response_data.get("data", {}).get("status", "unknown")
                    
                    # 3. Mapper le statut MPP vers notre statut
                    new_status = self.map_mpp_status(mpp_status)
                    
                    if new_status != transaction.status:
                        old_status = transaction.status
                        transaction.status = new_status
                        
                        # Mettre à jour aussi le statut MPP dans details
                        details["mpp_status"] = mpp_status
                        transaction.details = details
                        
                        transaction.save(update_fields=["status", "details", "updated_at"])
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✅ {transaction.reference}: {old_status} → {new_status} (MPP: {mpp_status})"
                            )
                        )
                    else:
                        self.stdout.write(f"   {transaction.reference}: Aucun changement ({transaction.status})")
                        
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  {transaction.reference}: Transaction introuvable sur MPP (ID: {mpp_transaction_id})")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ {transaction.reference}: Erreur HTTP {e.code}"
                        )
                    )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ {transaction.reference}: Erreur - {str(e)}")
            )

    def get_access_token(self):
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
        
        # POST request avec urllib
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url, 
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                access_token = response_data["data"]["access_token"]
                cache.set(cache_key, access_token, 25 * 60)  # 25 minutes
                return access_token
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise Exception(f"Authentication failed: {error_body}")

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
