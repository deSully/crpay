from django.contrib import admin
from django_filters import rest_framework as filters

from transaction.models import Transaction


class TransactionFilter(filters.FilterSet):
    invoice_type = filters.CharFilter(
        field_name="details__invoice_type", lookup_expr="iexact"
    )
    status = filters.CharFilter(field_name="status", lookup_expr="iexact")
    start_date = filters.DateFilter(field_name="created_at", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Transaction
        fields = ["invoice_type", "status", "start_date", "end_date"]
