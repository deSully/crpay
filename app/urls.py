from django.urls import path



from .views import dashboard, analytics, partners, payments, login

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("", dashboard, name="dashboard"),
    path("analytics/", analytics, name="analytics"),
    path("partners/", partners, name="partners"),
    path("payments/", payments, name="payments"),
    path("login/", login, name="login"),
]