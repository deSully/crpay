from django.urls import path


from .views import dashboard, analytics, partners, payments, login, password_reset, logout
from .api import (
    transaction_data_api, 
    payment_purpose_data_api,
    analytics_volume_chart_api,
    analytics_service_chart_api,
    analytics_status_chart_api
)

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("", dashboard, name="dashboard"),
    path("analytics/", analytics, name="analytics"),
    path("partners/", partners, name="partners"),
    path("payments/", payments, name="payments"),
    path("login/", login, name="login"),
    path("password_reset/", password_reset, name="password_reset"),
    path("logout/", logout, name="app-logout"),

    path("api/transactions-data/", transaction_data_api, name="transactions_data_api"),
    path("api/payment-purpose-data/", payment_purpose_data_api, name="payment_purpose_data_api"),
    path("api/analytics-volume/", analytics_volume_chart_api, name="analytics_volume_chart_api"),
    path("api/analytics-service/", analytics_service_chart_api, name="analytics_service_chart_api"),
    path("api/analytics-status/", analytics_status_chart_api, name="analytics_status_chart_api"),

]
