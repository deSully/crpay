from rest_framework import serializers

from transaction.models import Transaction


class TransactionCreateSerializer(serializers.Serializer):
    amount = serializers.FloatField()
    invoice_type = serializers.CharField()
    purpose = serializers.CharField()
    details = serializers.DictField()
    

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
