import logging

from django.utils.timezone import now
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from transaction.models import InTouchLog, Transaction

logger = logging.getLogger(__name__)


class InTouchCallbackView(APIView):
    @swagger_auto_schema(auto_schema=None)
    def post(self, request, *args, **kwargs):
        data = request.data
        logger.info("InTouch callback received: %s", data)

        reference = data.get("idFromClient")
        new_status = data.get(
            "status"
        )  # À adapter si le champ réel s'appelle autrement

        if not reference:
            logger.warning("Callback reçu sans 'idFromClient'.")
            return Response(
                {"error": "idFromClient est requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            transaction = Transaction.objects.get(reference=reference)
        except Transaction.DoesNotExist:
            logger.warning("Transaction avec référence %s non trouvée.", reference)
            return Response(
                {"error": "Transaction non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        if new_status and new_status.upper() in ["SUCCESS", "FAILED"]:
            transaction.status = new_status.upper()
            transaction.save(update_fields=["status", "updated_at"])
            logger.info(
                "Transaction %s mise à jour avec status=%s.", reference, new_status
            )
        else:
            logger.warning(
                "Status non reconnu ou manquant pour la transaction %s.", reference
            )

        # Mise à jour du status transaction
        if new_status and new_status.upper() in ["SUCCESS", "FAILED"]:
            transaction.status = new_status.upper()
            transaction.save(update_fields=["status", "updated_at"])

        # Mise à jour ou création du log
        InTouchLog.objects.update_or_create(
            transaction=transaction,
            defaults={
                "response_payload": data,
                "callback_received_at": now(),
                "status": new_status.upper() if new_status else "RECEIVED",
            },
        )

        return Response({"message": "Callback traité."}, status=status.HTTP_200_OK)
