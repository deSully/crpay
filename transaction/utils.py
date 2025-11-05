import os
import httpx
from django.core.cache import cache


class MerchantPaymentDispatcher:
    """
    Dispatcher pour Merchant Payment Platform API
    """
    BASE_URL = os.getenv("MPP_BASE_URL", "https://gateway.mpp.bnbcash.app")
    CACHE_KEY = "mpp_access_token"
    TOKEN_EXPIRY = 25 * 60  # 25 minutes (le token expire à 29 min)
    
    def __init__(self, transaction):
        self.transaction = transaction
        self.secret_id = os.environ["MPP_SECRET_ID"]
        self.secret_key = os.environ["MPP_SECRET_KEY"]
        self.business_id = os.environ["MPP_BUSINESS_ID"]
        self.channel = os.getenv("MPP_CHANNEL", "OM")  # Orange Money par défaut
        self.webhook_url = os.getenv("MPP_WEBHOOK_URL", "")

    async def get_access_token(self):
        """
        Obtenir un token d'accès (depuis le cache ou en se ré-authentifiant)
        """
        # 1. Vérifier si on a un token en cache
        cached_token = cache.get(self.CACHE_KEY)
        if cached_token:
            return cached_token
        
        # 2. Sinon, s'authentifier et cacher le token
        url = f"{self.BASE_URL}/api/auth/token"
        payload = {
            "secret_id": self.secret_id,
            "secret_key": self.secret_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=30.0)
            
            if response.status_code == 200:
                data = response.json()
                access_token = data["data"]["access_token"]
                
                # 3. Cacher le token pendant 25 minutes
                cache.set(self.CACHE_KEY, access_token, self.TOKEN_EXPIRY)
                
                return access_token
            else:
                raise Exception(f"Authentication failed: {response.text}")

    async def dispatch(self):
        """
        Créer une transaction sur Merchant Payment Platform
        """
        try:
            # 1. Obtenir le token (depuis cache ou authentification)
            access_token = await self.get_access_token()
            
            # 2. Préparer le payload
            details = self.transaction.details or {}
            
            # Vérifier les champs requis
            msisdn = details.get("phone_number")
            if not msisdn:
                raise ValueError("Le champ 'phone_number' est requis dans details")
            
            payload = {
                # Champs requis par MPP
                "business_id": self.business_id,
                "channel": self.channel,
                "external_id": str(self.transaction.reference),
                "currency": details.get("currency", "GNF"),  # XOF par défaut
                "category": details.get("category", "payment"),  # payment par défaut
                "amount": float(self.transaction.amount),
                "msisdn": msisdn,  # REQUIS - pas de valeur par défaut
            }
            
            # Ajouter account_number seulement s'il est fourni (pour éviter les strings vides)
            account_number = details.get("account_number")
            if account_number:
                payload["account_number"] = account_number
            
            # 3. Envoyer la transaction
            url = f"{self.BASE_URL}/api/v1/transaction"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, 
                    json=payload, 
                    headers=headers,
                    timeout=30.0
                )
            
            # 4. Traiter la réponse
            try:
                response_data = response.json()
            except Exception:
                response_data = {"error": f"Non-JSON response: {response.text}"}
            
            return {
                "status_code": response.status_code,
                "json": response_data,
                "payload_sent": payload,
                "external_id": response_data.get("data", {}).get("id"),  # ID de la transaction côté MPP
                "mpp_status": response_data.get("data", {}).get("status", "unknown")
            }
            
        except Exception as e:
            return {
                "status_code": 500,
                "json": {"error": str(e)},
                "payload_sent": payload if 'payload' in locals() else {},
                "external_id": None,
                "mpp_status": "error"
            }

