import logging

from django.utils.timezone import now
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from transaction.models import PaymentProviderLog, Transaction

logger = logging.getLogger(__name__)


class PaymentCallbackView(APIView):
    """
    Webhook pour recevoir les mises à jour de statut depuis Merchant Payment Platform
    """
    @swagger_auto_schema(auto_schema=None)
    def post(self, request, *args, **kwargs):
        data = request.data
        logger.info("MPP callback received: %s", data)

        # MPP envoie external_id (notre reference)
        reference = data.get("external_id") or data.get("idFromClient")  # Rétrocompat
        mpp_status = data.get("status", "").lower()

        if not reference:
            logger.warning("Callback reçu sans external_id.")
            return Response(
                {"error": "external_id est requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            transaction = Transaction.objects.get(reference=reference)
        except Transaction.DoesNotExist:
            logger.warning("Transaction avec référence %s non trouvée.", reference)
            return Response(
                {"error": "Transaction non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        # Mapper les statuts MPP vers nos statuts
        status_mapping = {
            "completed": "SUCCESS",
            "failed": "FAILED",
            "rejected": "FAILED",
            "cancelled": "FAILED",
            "initiated": "PENDING",
            "pending": "PENDING",
            "processing": "PENDING",
            "transmitted": "PENDING",
        }

        new_status = status_mapping.get(mpp_status)
        
        if new_status:
            transaction.status = new_status
            transaction.save(update_fields=["status", "updated_at"])
            logger.info(
                "Transaction %s mise à jour: %s → %s", 
                reference, mpp_status, new_status
            )
        else:
            logger.warning(
                "Status MPP non reconnu pour transaction %s: %s", 
                reference, mpp_status
            )

        # Logger le callback
        PaymentProviderLog.objects.update_or_create(
            transaction=transaction,
            defaults={
                "response_payload": data,
                "callback_received_at": now(),
                "status": "SUCCESS" if new_status == "SUCCESS" else "RECEIVED",
                "provider": "MPP",
            },
        )

        return Response({"message": "Callback traité."}, status=status.HTTP_200_OK)


# Alias pour rétrocompatibilité
InTouchCallbackView = PaymentCallbackView
