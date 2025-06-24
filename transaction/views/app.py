from django.shortcuts import render

def afficher_toto(request):
    return render(request, 'app/dashboard.html')
