from django.urls import path


from .views import dashboard, analytics, partners, payments, login, password_reset
from .api import transaction_data_api, payment_purpose_data_api

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("", dashboard, name="dashboard"),
    path("analytics/", analytics, name="analytics"),
    path("partners/", partners, name="partners"),
    path("payments/", payments, name="payments"),
    path("login/", login, name="login"),
    path("password_reset/", password_reset, name="password_reset"),
    path("logout/", login, name="logout"),

    path("api/transactions-data/", transaction_data_api, name="transactions_data_api"),
    path("api/payment-purpose-data/", payment_purpose_data_api, name="payment_purpose_data_api"),

]
