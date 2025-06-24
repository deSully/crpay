from django.urls import path



from .views import dashboard, analytics, partners

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("analytics/", analytics, name="analytics"),
    path("partners/", partners, name="partners"),
]