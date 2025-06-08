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
from transaction.models import InTouchLog, Transaction
from transaction.serializers import TransactionSerializer, TransactionCreateSerializer
from transaction.utils import ExternalTransactionDispatcher


class TransactionView(APIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = TransactionFilter
    ordering_fields = ["created_at", "amount"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        if user.entity.entity_type == "INTERNAL":
            return Transaction.objects.all()
        return Transaction.objects.filter(entity=user.entity)
    

    @swagger_auto_schema(
        operation_summary="Lister les paiements",
        operation_description="Récupère la liste des paiements associées à l'utilisateur connecté. Les utilisateurs internes voient tous les paiements.",
        responses={200: TransactionSerializer(many=True)},
        manual_parameters=[
            openapi.Parameter(
                'ordering', openapi.IN_QUERY, description="Ordre de tri (ex: -created_at)", type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'search', openapi.IN_QUERY, description="Recherche dans les champs autorisés", type=openapi.TYPE_STRING
            ),
        ]
    )

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(request, queryset, self)

        serializer = TransactionSerializer(queryset.order_by(*self.ordering), many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Créer un paiement",
        operation_description="Crée un paiement avec les informations fournies, et envoie automatiquement la requête vers le système externe en tâche de fond.",
        request_body=TransactionCreateSerializer,
        responses={
            201: openapi.Response(
                description="Paiement créé avec succès",
                examples={
                    "application/json": {
                        "message": "Paiement créé avec succès.",
                        "transaction": {
                            "uuid": "d66cfb4c-50cd-44bc-9600-ea5f91eaa21b",
                            "reference": "TX-ABCDEF1234",
                            "amount": "15000.0",
                            "status": "PENDING",
                            "details": {
                                "client_name": "Alice Dupont",
                                "order_id": "ORD-1023",
                                "invoice_type": "ACHAT"
                            },
                            "created_at": "2025-06-07T14:32:00Z"
                        }
                    }
                }
            ),
            400: "Erreur de validation"
        }
    )
    def post(self, request, *args, **kwargs):
        amount = request.data.get("amount")
        invoice_type = request.data.get("invoice_type")
        details = request.data.get("details")
        purpose = request.data.get("purpose")

        if not all([amount, invoice_type, details, purpose]):
            return Response(
                {
                    "error": "Le montant, le type de facture, le type de paiement et les détails sont requis."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            amount = float(amount)
        except ValueError:
            return Response(
                {"error": "Le montant doit être un nombre valide."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reference = f"TX-{uuid.uuid4().hex[:10].upper()}"
        entity = request.user.entity
        full_details = {**details, "invoice_type": invoice_type}

        transaction = Transaction.objects.create(
            purpose=purpose,
            reference=reference,
            entity=entity,
            amount=amount,
            details=full_details,
            status="PENDING",
        )

        def launch_dispatch_background(transaction):
            async def launch_dispatch():
                dispatcher = ExternalTransactionDispatcher(
                    reference=transaction.reference,
                    amount=transaction.amount,
                    details=transaction.details,
                )
                response = await dispatcher.dispatch()

                InTouchLog.objects.update_or_create(
                    transaction=transaction,
                    defaults={
                        "request_payload": response["payload_sent"],
                        "response_payload": response["json"],
                        "http_status": response["status_code"],
                        "status": "SENT"
                        if response["status_code"] in (200, 202)
                        else "FAILED",
                        "sent_at": now(),
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
