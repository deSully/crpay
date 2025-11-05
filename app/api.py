from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils.timezone import now
from datetime import timedelta
from transaction.models import Transaction

@require_GET
@login_required
def transaction_data_api(request):
    period = request.GET.get("period", "this_month")  # ce mois ou le mois dernier
    today = now().date()
    start_of_month = today.replace(day=1)
    start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)
    end_of_last_month = start_of_month - timedelta(days=1)

    # Si superuser ou staff (PROVIDER) = voir toutes les transactions
    # Sinon = voir uniquement les transactions de son entité
    if request.user.is_superuser or request.user.is_staff:
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
    else:
        user_entity = request.user.entity
        if period == "last_month":
            queryset = Transaction.objects.filter(
                entity=user_entity,
                created_at__date__gte=start_of_last_month,
                created_at__date__lte=end_of_last_month,
                status="SUCCESS"
            )
        else:
            queryset = Transaction.objects.filter(
                entity=user_entity,
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
@login_required
def payment_purpose_data_api(request):
    period = request.GET.get("period", "this_month")
    today = now().date()
    start_of_month = today.replace(day=1)
    start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)
    end_of_last_month = start_of_month - timedelta(days=1)

    # Si superuser ou staff (PROVIDER) = voir toutes les transactions
    # Sinon = voir uniquement les transactions de son entité
    if request.user.is_superuser or request.user.is_staff:
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
    else:
        user_entity = request.user.entity
        if period == "last_month":
            queryset = Transaction.objects.filter(
                entity=user_entity,
                created_at__date__gte=start_of_last_month,
                created_at__date__lte=end_of_last_month,
                status="SUCCESS"
            )
        else:
            queryset = Transaction.objects.filter(
                entity=user_entity,
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

    labels = [entry['purpose'] or "Autre" for entry in data]
    values = [float(entry['total']) for entry in data]

    return JsonResponse({
        "labels": labels,
        "data": values
    })


@require_GET
@login_required
def analytics_volume_chart_api(request):
    """API pour le graphique de volume de transactions (quotidien, hebdomadaire, mensuel)"""
    from django.utils.dateparse import parse_date
    from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
    
    # Récupérer les paramètres
    period_type = request.GET.get('period', 'daily')  # daily, weekly, monthly
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    service_filter = request.GET.get('service')
    entity_filter = request.GET.get('entity')
    
    # Définir les dates par défaut (ce mois)
    today = now().date()
    if not start_date:
        start_date = today.replace(day=1)
    else:
        start_date = parse_date(start_date)
    
    if not end_date:
        end_date = today
    else:
        end_date = parse_date(end_date)
    
    # Construire le queryset de base selon l'utilisateur
    if request.user.is_superuser or request.user.is_staff:
        queryset = Transaction.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        if service_filter:
            queryset = queryset.filter(purpose=service_filter)
        if entity_filter:
            queryset = queryset.filter(entity_id=entity_filter)
    else:
        user_entity = request.user.entity
        queryset = Transaction.objects.filter(
            entity=user_entity,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        if service_filter:
            queryset = queryset.filter(purpose=service_filter)
    
    # Grouper selon la période
    if period_type == 'weekly':
        data = (
            queryset
            .annotate(period=TruncWeek('created_at'))
            .values('period')
            .annotate(total=Sum('amount'), count=Count('uuid'))
            .order_by('period')
        )
        labels = [entry['period'].strftime('%d %b') if entry['period'] else '' for entry in data]
    elif period_type == 'monthly':
        data = (
            queryset
            .annotate(period=TruncMonth('created_at'))
            .values('period')
            .annotate(total=Sum('amount'), count=Count('uuid'))
            .order_by('period')
        )
        labels = [entry['period'].strftime('%b %Y') if entry['period'] else '' for entry in data]
    else:  # daily
        data = (
            queryset
            .annotate(period=TruncDate('created_at'))
            .values('period')
            .annotate(total=Sum('amount'), count=Count('uuid'))
            .order_by('period')
        )
        labels = [entry['period'].strftime('%d/%m') if entry['period'] else '' for entry in data]
    
    values = [float(entry['total']) if entry['total'] else 0 for entry in data]
    counts = [entry['count'] for entry in data]
    
    return JsonResponse({
        'labels': labels,
        'data': values,
        'counts': counts
    })


@require_GET
@login_required
def analytics_service_chart_api(request):
    """API pour le graphique des paiements par service"""
    from django.utils.dateparse import parse_date
    
    # Récupérer les paramètres de filtre
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    service_filter = request.GET.get('service')
    entity_filter = request.GET.get('entity')
    
    # Définir les dates par défaut (ce mois)
    today = now().date()
    if not start_date:
        start_date = today.replace(day=1)
    else:
        start_date = parse_date(start_date)
    
    if not end_date:
        end_date = today
    else:
        end_date = parse_date(end_date)
    
    # Construire le queryset selon l'utilisateur
    if request.user.is_superuser or request.user.is_staff:
        queryset = Transaction.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            status='SUCCESS'
        )
        if service_filter:
            queryset = queryset.filter(purpose=service_filter)
        if entity_filter:
            queryset = queryset.filter(entity_id=entity_filter)
    else:
        user_entity = request.user.entity
        queryset = Transaction.objects.filter(
            entity=user_entity,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            status='SUCCESS'
        )
        if service_filter:
            queryset = queryset.filter(purpose=service_filter)
    
    # Grouper par service
    data = (
        queryset
        .values('purpose')
        .annotate(total=Sum('amount'))
        .order_by('-total')[:10]  # Top 10 services
    )
    
    labels = [entry['purpose'] or 'Autre' for entry in data]
    values = [float(entry['total']) if entry['total'] else 0 for entry in data]
    
    return JsonResponse({
        'labels': labels,
        'data': values
    })


@require_GET
@login_required
def analytics_status_chart_api(request):
    """API pour le graphique des statuts de paiement"""
    from django.utils.dateparse import parse_date
    from django.db.models import Count
    
    # Récupérer les paramètres de filtre
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    service_filter = request.GET.get('service')
    entity_filter = request.GET.get('entity')
    
    # Définir les dates par défaut (ce mois)
    today = now().date()
    if not start_date:
        start_date = today.replace(day=1)
    else:
        start_date = parse_date(start_date)
    
    if not end_date:
        end_date = today
    else:
        end_date = parse_date(end_date)
    
    # Construire le queryset selon l'utilisateur
    if request.user.is_superuser or request.user.is_staff:
        queryset = Transaction.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        if service_filter:
            queryset = queryset.filter(purpose=service_filter)
        if entity_filter:
            queryset = queryset.filter(entity_id=entity_filter)
    else:
        user_entity = request.user.entity
        queryset = Transaction.objects.filter(
            entity=user_entity,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        if service_filter:
            queryset = queryset.filter(purpose=service_filter)
    
    # Grouper par statut
    data = (
        queryset
        .values('status')
        .annotate(count=Count('uuid'))
        .order_by('-count')
    )
    
    status_labels = {
        'SUCCESS': 'Réussie',
        'PENDING': 'En attente',
        'FAILED': 'Échouée'
    }
    
    labels = [status_labels.get(entry['status'], entry['status']) for entry in data]
    values = [entry['count'] for entry in data]
    
    return JsonResponse({
        'labels': labels,
        'data': values
    })