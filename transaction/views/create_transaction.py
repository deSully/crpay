import asyncio
import threading
import uuid

from django.utils.timezone import now
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from transaction.models import InTouchLog, Transaction
from transaction.utils import ExternalTransactionDispatcher


class CreateTransactionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        amount = request.data.get("amount")
        invoice_type = request.data.get("invoice_type")
        details = request.data.get("details")
        purpose = request.data.get("purpose")

        if not all([amount, invoice_type, details, purpose]):
            return Response(
                {
                    "error": "Le montant, le type de facture, le purpose et les détails sont requis."
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
        entity = request.user

        # On enrichit les détails avec invoice_type
        full_details = {**details, "invoice_type": invoice_type}

        # Création de la transaction
        transaction = Transaction.objects.create(
            purpose=purpose,
            reference=reference,
            entity=entity,
            amount=amount,
            details=full_details,
            status="PENDING",
        )

        # Fonction de dispatch async lancée en tâche de fond via threading
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

        # Démarrage de la tâche async en arrière-plan
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
