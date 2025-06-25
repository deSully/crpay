
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

def login(request):
    """
    Render the login page.
    """
    return render(request, 'app/login.html')

def password_reset(request):
    """
    Render the password reset page.
    """
    return render(request, 'app/password_reset.html')

def logout(request):
    """
    Render the logout page.
    """
    return render(request, 'app/logout.html')