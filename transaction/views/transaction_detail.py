from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from transaction.models import Transaction
from transaction.serializers import TransactionSerializer


class TransactionDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        user = self.request.user
        if user.entity.entity_type == "INTERNAL":
            return Transaction.objects.all()
        return Transaction.objects.filter(entity=user.entity)

    @swagger_auto_schema(
        operation_summary="Détails d'une transaction",
        operation_description="Permet de consulter l'état actuel d'une transaction grâce à son UUID. Utile pour vérifier l'état après un traitement asynchrone ou un callback.",
        responses={
            200: TransactionSerializer(),
            404: "Transaction non trouvée ou non autorisée.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
