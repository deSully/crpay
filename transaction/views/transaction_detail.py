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
        operation_summary="Consulter une transaction",
        operation_description="""
Récupère les détails complets d'une transaction spécifique.

**Utilisation :**
- Utilisez l'UUID retourné lors de la création
- Permet de vérifier le statut actuel (PENDING, SUCCESS, FAILED)
- Consultez les détails de traitement et timestamps

**Exemple :**
```
GET /api/v0/payments/d66cfb4c-50cd-44bc-9600-ea5f91eaa21b/
```

**Statuts possibles :**
- `PENDING` : En attente de traitement
- `SUCCESS` : Paiement réussi
- `FAILED` : Paiement échoué
        """,
        responses={
            200: TransactionSerializer(),
            404: "Transaction non trouvée",
            401: "Non authentifié"
        },
        tags=["💳 Paiements"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
