from django.urls import path

from .views.intouch_callback import InTouchCallbackView
from .views.transaction import TransactionView

urlpatterns = [
    path("", TransactionView.as_view(), name="create_transaction"),
    path("callback", InTouchCallbackView.as_view(), name="intouch-callback"),
]
