from django.urls import path

from .views.login import EntityLoginView

urlpatterns = [
    path("auth/", EntityLoginView.as_view(), name="entity-login"),
]
