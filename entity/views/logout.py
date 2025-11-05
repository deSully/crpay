from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "POST"])
def admin_logout_view(request):
    """
    Custom logout view that accepts both GET and POST for admin logout
    """
    logout(request)
    return redirect('admin:login')
