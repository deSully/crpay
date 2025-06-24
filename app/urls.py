from django.urls import path



from .views import dashboard, analytics

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("analytics/", analytics, name="analytics"),
    path("partners/", analytics, name="partners"),
]