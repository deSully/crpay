from django.shortcuts import render
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Sum
from transaction.models import Transaction
from django.core.paginator import Paginator
from django.db.models import Avg
from datetime import datetime


def dashboard(request):
    today = now().date()
    start_of_month = today.replace(day=1)
    start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)

    # Montant et nombre ce mois
    this_month_tx = Transaction.objects.filter(created_at__date__gte=start_of_month)
    last_month_tx = Transaction.objects.filter(
        created_at__date__gte=start_of_last_month, created_at__date__lt=start_of_month
    )

    total_monthly_amount = this_month_tx.aggregate(Sum("amount"))["amount__sum"] or 0
    last_month_amount = last_month_tx.aggregate(Sum("amount"))["amount__sum"] or 0

    total_monthly_count = this_month_tx.count()
    last_month_count = last_month_tx.count()

    # Paiements aujourd’hui
    daily_tx = Transaction.objects.filter(created_at__date=today)
    daily_amount = daily_tx.aggregate(Sum("amount"))["amount__sum"] or 0
    daily_count = daily_tx.count()

    # Calcul croissance
    monthly_growth = (
        round(((total_monthly_amount - last_month_amount) / last_month_amount) * 100, 2)
        if last_month_amount
        else 0
    )
    monthly_tx_growth = (
        round(((total_monthly_count - last_month_count) / last_month_count) * 100, 2)
        if last_month_count
        else 0
    )

    context = {
        "total_monthly_amount": total_monthly_amount,
        "total_monthly_count": total_monthly_count,
        "daily_amount": daily_amount,
        "daily_count": daily_count,
        "monthly_growth": monthly_growth,
        "monthly_tx_growth": monthly_tx_growth,
        "last_update": now(),
    }

    latest_transactions = Transaction.objects.order_by("-created_at")[:5]
    context["latest_transactions"] = latest_transactions

    return render(request, "app/dashboard.html", context)


def analytics(request):
    today = datetime.today()
    start_month = today.replace(day=1)
    last_month_start = (start_month - timedelta(days=1)).replace(day=1)
    last_month_end = start_month - timedelta(days=1)

    # Total de paiements ce mois (nombre)
    total_payments = Transaction.objects.filter(created_at__gte=start_month).count()

    # Volume total des paiements ce mois (somme des montants)
    total_amount = Transaction.objects.filter(created_at__gte=start_month).aggregate(
        total=Sum("amount")
    )["total"]

    # Somme moyenne payée ce mois
    average_amount = Transaction.objects.filter(created_at__gte=start_month).aggregate(
        avg=Avg("amount")
    )["avg"]

    # Taux de succès : % de transactions avec status success ce mois
    total_tx = Transaction.objects.filter(created_at__gte=start_month).count()
    success_tx = Transaction.objects.filter(
        created_at__gte=start_month, status="SUCCESS"
    ).count()
    success_rate = (success_tx / total_tx * 100) if total_tx > 0 else 0

    # Calcul % d’évolution par rapport au mois dernier
    def calc_percent_change(current, previous):
        if previous in [None, 0]:
            return 0
        return round((current - previous) / previous * 100, 1)

    # Valeurs mois dernier
    last_month_payments = Transaction.objects.filter(
        created_at__gte=last_month_start, created_at__lte=last_month_end
    ).count()
    last_month_amount = Transaction.objects.filter(
        created_at__gte=last_month_start, created_at__lte=last_month_end
    ).aggregate(total=Sum("amount"))["total"]
    last_month_avg = Transaction.objects.filter(
        created_at__gte=last_month_start, created_at__lte=last_month_end
    ).aggregate(avg=Avg("amount"))["avg"]
    last_month_success_tx = Transaction.objects.filter(
        created_at__gte=last_month_start,
        created_at__lte=last_month_end,
        status="SUCCESS",
    ).count()
    last_month_total_tx = Transaction.objects.filter(
        created_at__gte=last_month_start, created_at__lte=last_month_end
    ).count()
    last_month_success_rate = (
        (last_month_success_tx / last_month_total_tx * 100)
        if last_month_total_tx > 0
        else 0
    )

    context = {
        "total_payments": total_payments,
        "total_amount": total_amount,
        "average_amount": average_amount,
        "success_rate": f"{success_rate:.1f}%",
        "total_payments_change": calc_percent_change(
            total_payments, last_month_payments
        ),
        "total_amount_change": calc_percent_change(
            total_amount or 0, last_month_amount or 0
        ),
        "average_amount_change": calc_percent_change(
            average_amount or 0, last_month_avg or 0
        ),
        "success_rate_change": calc_percent_change(
            success_rate, last_month_success_rate
        ),
    }
    return render(request, "app/analytics.html", context)


def partners(request):
    """
    Render the partners page.
    """
    return render(request, "app/partners.html")


def payments(request):
    transactions = Transaction.objects.select_related("entity").order_by("-created_at")
    paginator = Paginator(transactions, 10)  # 10 transactions par page

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
    }
    return render(request, "app/payments.html", context)


def login(request):
    """
    Render the login page.
    """
    return render(request, "app/login.html")


def password_reset(request):
    """
    Render the password reset page.
    """
    return render(request, "app/password_reset.html")


def logout(request):
    """
    Render the logout page.
    """
    return render(request, "app/logout.html")
