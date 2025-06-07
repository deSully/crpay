from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import (
    OrderingFilter,
    SearchFilter,
)  # 👈 ajoute SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from transaction.filters import TransactionFilter  # le filtre défini plus haut
from transaction.models import Transaction
from transaction.serializers import TransactionSerializer


class TransactionListView(ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = TransactionFilter
    ordering_fields = ["created_at", "amount"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        if user.entity_type == "INTERNAL":
            return Transaction.objects.all()
        return Transaction.objects.filter(entity=user)
