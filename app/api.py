from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Sum
from django.utils.timezone import now
from datetime import timedelta
from transaction.models import Transaction

@require_GET
def transaction_data_api(request):
    period = request.GET.get("period", "this_month")  # ce mois ou le mois dernier
    today = now().date()
    start_of_month = today.replace(day=1)
    start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)
    end_of_last_month = start_of_month - timedelta(days=1)

    if period == "last_month":
        queryset = Transaction.objects.filter(
            created_at__date__gte=start_of_last_month,
            created_at__date__lte=end_of_last_month,
            status="SUCCESS"
        )
    else:
        queryset = Transaction.objects.filter(
            created_at__date__gte=start_of_month,
            created_at__date__lte=today,
            status="SUCCESS"
        )

    # Regrouper par jour
    data = (
        queryset
        .extra(select={'day': "DATE(created_at)"})
        .values('day')
        .annotate(total=Sum("amount"))
        .order_by('day')
    )

    labels = [entry["day"].strftime("%d %b") for entry in data]
    values = [float(entry["total"]) for entry in data]

    return JsonResponse({
        "labels": labels,
        "data": values
    })


@require_GET
def payment_purpose_data_api(request):
    period = request.GET.get("period", "this_month")
    today = now().date()
    start_of_month = today.replace(day=1)
    start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)
    end_of_last_month = start_of_month - timedelta(days=1)

    if period == "last_month":
        queryset = Transaction.objects.filter(
            created_at__date__gte=start_of_last_month,
            created_at__date__lte=end_of_last_month,
            status="SUCCESS"
        )
    else:
        queryset = Transaction.objects.filter(
            created_at__date__gte=start_of_month,
            created_at__date__lte=today,
            status="SUCCESS"
        )

    data = (
        queryset
        .values('purpose')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    labels = [entry['purpose'] or "Autre"] for entry in data]
    values = [float(entry['total']) for entry in data]

    return JsonResponse({
        "labels": labels,
        "data": values
    })