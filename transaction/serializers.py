from rest_framework import serializers

from transaction.models import Transaction


class TransactionCreateSerializer(serializers.Serializer):
    amount = serializers.FloatField(
        help_text="Montant de la transaction en XOF"
    )
    phone_number = serializers.CharField(
        help_text="Numéro de téléphone du client au format local (ex: 0770123456)",
        required=True
    )
    service = serializers.CharField(
        help_text="Description du service/produit"
    )
    details = serializers.DictField(
        help_text="Données additionnelles (order_id, customer_name, etc.)",
        required=False
    )
    

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "uuid",
            "reference",
            "amount",
            "status",
            "details",
            "created_at",
            "updated_at",
        ]
