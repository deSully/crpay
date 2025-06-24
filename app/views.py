
from django.shortcuts import render

def dashboard(request):
    """
    Render the dashboard page.
    """
    return render(request, 'app/dashboard.html')

def analytics(request):
    """
    Render the analytics page.
    """
    return render(request, 'app/analytics.html')

def partners(request):
    """
    Render the partners page.
    """
    return render(request, 'app/partners.html')

def payments(request):
    """
    Render the payments page.
    """
    return render(request, 'app/payments.html')