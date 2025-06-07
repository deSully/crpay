from django.urls import path

from .views.login import EntityLoginView

urlpatterns = [
    path("login/", EntityLoginView.as_view(), name="entity-login"),
]
