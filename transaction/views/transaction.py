import asyncio
import threading
import uuid

from django.utils.timezone import now
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from transaction.filters import TransactionFilter
from transaction.models import PaymentProviderLog, Transaction
from transaction.serializers import TransactionSerializer, TransactionCreateSerializer
from transaction.utils import MerchantPaymentDispatcher


class TransactionView(APIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = TransactionFilter
    ordering_fields = ["created_at", "amount"]
    ordering = ["-created_at"]
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def get_queryset(self):
        user = self.request.user
        if user.entity.entity_type == "INTERNAL":
            return Transaction.objects.all()
        return Transaction.objects.filter(entity=user.entity)
    

    @swagger_auto_schema(
        operation_summary="Lister vos transactions",
        operation_description="""
Récupère l'historique de toutes vos transactions.

**Filtres disponibles :**
- Par date : `created_at__gte=2025-01-01`
- Par statut : `status=SUCCESS`
- Par montant : `amount__gte=1000`

**Tri disponible :**
- Par date : `ordering=-created_at` (plus récent en premier)
- Par montant : `ordering=-amount`

**Exemple :**
```
GET /api/v0/payments/?status=PENDING&ordering=-created_at
```
        """,
        responses={
            200: TransactionSerializer(many=True),
            401: "Non authentifié"
        },
        manual_parameters=[
            openapi.Parameter(
                'ordering', 
                openapi.IN_QUERY, 
                description="Tri : -created_at (desc), created_at (asc), -amount, amount", 
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'status', 
                openapi.IN_QUERY, 
                description="Filtrer par statut : PENDING, SUCCESS, FAILED", 
                type=openapi.TYPE_STRING,
                enum=["PENDING", "SUCCESS", "FAILED"]
            ),
        ],
        tags=["💳 Paiements"]
    )

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(request, queryset, self)

        serializer = TransactionSerializer(queryset.order_by(*self.ordering), many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Initier un paiement",
        operation_description="""
Crée une nouvelle transaction de paiement. Le traitement est **asynchrone** : 
vous recevrez une réponse immédiate, puis un callback sur votre webhook.

**Paramètres requis :**
- `amount` : Montant en XOF (ex: 5000)
- `phone_number` : Numéro du client au format local (ex: 0770123456)
- `service` : Type de service (ex: "Achat en ligne", "Paiement facture")

**Paramètres optionnels :**
- `details` : Objet JSON contenant des données additionnelles (order_id, customer_name, currency, category, etc.)

**Flux de traitement :**
1. La transaction est créée avec le statut `PENDING`
2. L'appel au provider de paiement est fait en arrière-plan
3. Vous recevez un UUID pour suivre la transaction
4. Le statut final (`SUCCESS` ou `FAILED`) vous sera notifié via callback

**Exemple de requête :**
```json
{
  "amount": 5000,
  "phone_number": "0770123456",
  "service": "Achat boutique en ligne",
  "details": {
    "order_id": "CMD-12345",
    "customer_name": "Jean Dupont",
    "currency": "XOF",
    "category": "payment"
  }
}
```
        """,
        request_body=TransactionCreateSerializer,
        responses={
            201: openapi.Response(
                description="Transaction créée avec succès",
                examples={
                    "application/json": {
                        "message": "Transaction créée avec succès.",
                        "transaction": {
                            "uuid": "d66cfb4c-50cd-44bc-9600-ea5f91eaa21b",
                            "reference": "TX-ABCDEF1234",
                            "amount": "5000.0",
                            "status": "PENDING",
                            "details": {
                                "phone_number": "0770123456",
                                "service": "Achat boutique en ligne",
                                "order_id": "CMD-12345",
                                "customer_name": "Jean Dupont",
                                "currency": "XOF",
                                "category": "payment"
                            },
                            "created_at": "2025-11-04T14:32:00Z"
                        }
                    }
                }
            ),
            400: "Paramètres manquants ou invalides",
            401: "Non authentifié"
        },
        tags=["💳 Paiements"]
    )
    def post(self, request, *args, **kwargs):
        # Valider avec le serializer
        serializer = TransactionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Extraire les données validées
        amount = serializer.validated_data["amount"]
        phone_number = serializer.validated_data["phone_number"]
        service = serializer.validated_data["service"]
        details = serializer.validated_data.get("details", {})

        reference = f"TX-{uuid.uuid4().hex[:10].upper()}"
        entity = request.user.entity
        
        # Construire les details avec phone_number pour MPP
        full_details = {
            **details, 
            "service": service, 
            "phone_number": phone_number
        }

        transaction = Transaction.objects.create(
            purpose=service,
            reference=reference,
            entity=entity,
            amount=amount,
            details=full_details,
            status="PENDING",
        )

        def launch_dispatch_background(transaction):
            async def launch_dispatch():
                dispatcher = MerchantPaymentDispatcher(transaction)
                response = await dispatcher.dispatch()

                PaymentProviderLog.objects.update_or_create(
                    transaction=transaction,
                    defaults={
                        "request_payload": response["payload_sent"],
                        "response_payload": response["json"],
                        "http_status": response["status_code"],
                        "status": "SENT"
                        if response["status_code"] in (200, 202)
                        else "FAILED",
                        "sent_at": now(),
                        "provider": "MPP",
                    },
                )

            asyncio.run(launch_dispatch())

        threading.Thread(target=launch_dispatch_background, args=(transaction,)).start()

        return Response(
            {
                "message": "Transaction créée avec succès.",
                "transaction": {
                    "uuid": str(transaction.uuid),
                    "reference": transaction.reference,
                    "amount": str(transaction.amount),
                    "status": transaction.status,
                    "details": transaction.details,
                    "created_at": transaction.created_at,
                },
            },
            status=status.HTTP_201_CREATED,
        )
