from django.shortcuts import render
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Sum
from transaction.models import Transaction
from django.core.paginator import Paginator
from django.db.models import Avg
from datetime import datetime
from django.contrib.auth.decorators import login_required


@login_required(login_url='/app/login/')
def dashboard(request):
    today = now().date()
    start_of_month = today.replace(day=1)
    start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)

    # Si superuser ou staff (PROVIDER) = voir toutes les transactions
    # Sinon = voir uniquement les transactions de son entité
    if request.user.is_superuser or request.user.is_staff:
        this_month_tx = Transaction.objects.filter(created_at__date__gte=start_of_month)
        last_month_tx = Transaction.objects.filter(
            created_at__date__gte=start_of_last_month,
            created_at__date__lt=start_of_month
        )
    else:
        user_entity = request.user.entity
        this_month_tx = Transaction.objects.filter(
            entity=user_entity,
            created_at__date__gte=start_of_month
        )
        last_month_tx = Transaction.objects.filter(
            entity=user_entity,
            created_at__date__gte=start_of_last_month,
            created_at__date__lt=start_of_month
        )

    total_monthly_amount = this_month_tx.aggregate(Sum("amount"))["amount__sum"] or 0
    last_month_amount = last_month_tx.aggregate(Sum("amount"))["amount__sum"] or 0

    total_monthly_count = this_month_tx.count()
    last_month_count = last_month_tx.count()

    # Paiements aujourd'hui
    if request.user.is_superuser or request.user.is_staff:
        daily_tx = Transaction.objects.filter(created_at__date=today)
    else:
        daily_tx = Transaction.objects.filter(entity=user_entity, created_at__date=today)
    
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

    if request.user.is_superuser or request.user.is_staff:
        latest_transactions = Transaction.objects.order_by("-created_at")[:5]
    else:
        latest_transactions = Transaction.objects.filter(entity=user_entity).order_by("-created_at")[:5]
    
    context["latest_transactions"] = latest_transactions

    return render(request, "app/dashboard.html", context)


@login_required(login_url='/app/login/')
def analytics(request):
    # Récupérer les paramètres de filtrage
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    service_filter = request.GET.get('service')
    entity_filter = request.GET.get('entity')
    
    today = datetime.today()
    start_month = today.replace(day=1)
    last_month_start = (start_month - timedelta(days=1)).replace(day=1)
    last_month_end = start_month - timedelta(days=1)
    
    # Construire le filtre de base selon les dates
    if start_date and end_date:
        from django.utils.dateparse import parse_date
        date_start = parse_date(start_date)
        date_end = parse_date(end_date)
        if date_start and date_end:
            start_month = date_start
            # Pour le mois dernier, on prend la même période mais un mois avant
            period_length = (date_end - date_start).days
            last_month_end = date_start - timedelta(days=1)
            last_month_start = last_month_end - timedelta(days=period_length)
    
    # Si superuser ou staff (PROVIDER) = voir toutes les transactions
    # Sinon = voir uniquement les transactions de son entité
    if request.user.is_superuser or request.user.is_staff:
        # PROVIDER voit tout - Construire le queryset de base
        current_qs = Transaction.objects.filter(created_at__gte=start_month)
        if end_date and date_end:
            current_qs = current_qs.filter(created_at__lte=date_end)
        
        # Appliquer les filtres supplémentaires
        if service_filter:
            current_qs = current_qs.filter(purpose=service_filter)
        if entity_filter:
            current_qs = current_qs.filter(entity_id=entity_filter)
        
        total_payments = current_qs.count()
        total_amount = current_qs.aggregate(total=Sum("amount"))["total"]
        average_amount = current_qs.aggregate(avg=Avg("amount"))["avg"]
        total_tx = current_qs.count()
        success_tx = current_qs.filter(status="SUCCESS").count()
        
        # Charger la liste des entités (MERCHANT et CLIENT) pour le filtre
        from entity.models import Entity
        entities = Entity.objects.filter(entity_type__in=["MERCHANT", "CLIENT"], is_active=True).order_by('name')
        
        # Récupérer la liste des services distincts utilisés dans les transactions
        services = Transaction.objects.values_list('purpose', flat=True).distinct().order_by('purpose')
        services = [s for s in services if s]  # Enlever les valeurs None ou vides
    else:
        # CLIENT voit uniquement ses transactions
        user_entity = request.user.entity
        current_qs = Transaction.objects.filter(entity=user_entity, created_at__gte=start_month)
        if end_date and date_end:
            current_qs = current_qs.filter(created_at__lte=date_end)
        
        # Appliquer le filtre de service
        if service_filter:
            current_qs = current_qs.filter(purpose=service_filter)
        
        total_payments = current_qs.count()
        total_amount = current_qs.aggregate(total=Sum("amount"))["total"]
        average_amount = current_qs.aggregate(avg=Avg("amount"))["avg"]
        total_tx = current_qs.count()
        success_tx = current_qs.filter(status="SUCCESS").count()
        
        # Pour les clients, pas de liste d'entités (ils ne voient que leurs données)
        entities = []
        
        # Récupérer les services distincts de l'entité du client
        services = Transaction.objects.filter(entity=user_entity).values_list('purpose', flat=True).distinct().order_by('purpose')
        services = [s for s in services if s]
    success_rate = (success_tx / total_tx * 100) if total_tx > 0 else 0

    # Calcul % d’évolution par rapport au mois dernier
    def calc_percent_change(current, previous):
        if previous in [None, 0]:
            return 0
        return round((current - previous) / previous * 100, 1)

    # Valeurs mois dernier - avec les mêmes filtres
    if request.user.is_superuser or request.user.is_staff:
        # PROVIDER voit tout
        last_qs = Transaction.objects.filter(created_at__gte=last_month_start, created_at__lte=last_month_end)
        if service_filter:
            last_qs = last_qs.filter(purpose=service_filter)
        if entity_filter:
            last_qs = last_qs.filter(entity_id=entity_filter)
        
        last_month_payments = last_qs.count()
        last_month_amount = last_qs.aggregate(total=Sum("amount"))["total"]
        last_month_avg = last_qs.aggregate(avg=Avg("amount"))["avg"]
        last_month_success_tx = last_qs.filter(status="SUCCESS").count()
        last_month_total_tx = last_qs.count()
    else:
        # CLIENT voit uniquement ses transactions
        last_qs = Transaction.objects.filter(entity=user_entity, created_at__gte=last_month_start, created_at__lte=last_month_end)
        if service_filter:
            last_qs = last_qs.filter(purpose=service_filter)
        
        last_month_payments = last_qs.count()
        last_month_amount = last_qs.aggregate(total=Sum("amount"))["total"]
        last_month_avg = last_qs.aggregate(avg=Avg("amount"))["avg"]
        last_month_success_tx = last_qs.filter(status="SUCCESS").count()
        last_month_total_tx = last_qs.count()
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
        "entities": entities,  # Liste des partenaires pour le filtre
        "services": services,  # Liste des services distincts
        # Valeurs du filtre pour les remettre dans le formulaire
        "selected_start_date": start_date or '',
        "selected_end_date": end_date or '',
        "selected_service": service_filter or '',
        "selected_entity": entity_filter or '',
    }
    return render(request, "app/analytics.html", context)


@login_required(login_url='/app/login/')
def partners(request):
    """
    Render the partners page - Only for staff and superusers.
    """
    from django.shortcuts import redirect
    from django.contrib import messages
    
    # Vérifier si l'utilisateur est staff ou superuser
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect('dashboard')
    
    return render(request, "app/partners.html")


@login_required(login_url='/app/login/')
def payments(request):
    # Si superuser ou staff (PROVIDER) = voir toutes les transactions
    # Sinon = voir uniquement les transactions de son entité
    if request.user.is_superuser or request.user.is_staff:
        transactions = Transaction.objects.select_related("entity").order_by("-created_at")
    else:
        user_entity = request.user.entity
        transactions = Transaction.objects.filter(entity=user_entity).select_related("entity").order_by("-created_at")
    
    paginator = Paginator(transactions, 10)  # 10 transactions par page

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
    }
    return render(request, "app/payments.html", context)


def login(request):
    """
    Render the login page and handle login POST requests.
    """
    if request.method == 'POST':
        import json
        from django.contrib.auth import authenticate, login as auth_login
        from django.http import JsonResponse
        
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return JsonResponse(
                    {'error': 'Le nom d\'utilisateur et le mot de passe sont requis.'},
                    status=400
                )
            
            user = authenticate(request, username=username, password=password)
            
            if user is None:
                return JsonResponse(
                    {'error': 'Identifiants invalides.'},
                    status=400
                )
            
            if not user.is_active:
                return JsonResponse(
                    {'error': 'Le compte utilisateur est inactif.'},
                    status=400
                )
            
            # Check if user has an entity
            entity = getattr(user, 'entity', None)
            if entity is None:
                return JsonResponse(
                    {'error': 'Aucune entité liée à cet utilisateur.'},
                    status=404
                )
            
            if not entity.is_active:
                return JsonResponse(
                    {'error': 'L\'entité liée est inactivée.'},
                    status=400
                )
            
            # Create Django session
            auth_login(request, user)
            
            return JsonResponse({
                'success': True,
                'message': 'Connexion réussie',
                'redirect': '/app/'
            }, status=200)
            
        except json.JSONDecodeError:
            return JsonResponse(
                {'error': 'Format de données invalide.'},
                status=400
            )
        except Exception as e:
            return JsonResponse(
                {'error': f'Erreur lors de la connexion: {str(e)}'},
                status=500
            )
    
    return render(request, "app/login.html")


def password_reset(request):
    """
    Render the password reset page.
    """
    return render(request, "app/password_reset.html")


def logout(request):
    """
    Logout the user and redirect to login page.
    """
    from django.contrib.auth import logout as auth_logout
    from django.shortcuts import redirect
    
    auth_logout(request)
    return redirect('login')
