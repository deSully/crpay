from django.urls import path


from .views import dashboard, analytics, partners, payments, login, password_reset

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("", dashboard, name="dashboard"),
    path("analytics/", analytics, name="analytics"),
    path("partners/", partners, name="partners"),
    path("payments/", payments, name="payments"),
    path("login/", login, name="login"),
    path("password_reset/", password_reset, name="password_reset"),
    path("logout/", login, name="logout"),
]
