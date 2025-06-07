from django.urls import path

from .views.create_transaction import CreateTransactionView
from .views.intouch_callback import InTouchCallbackView
from .views.list_transactions import TransactionListView

urlpatterns = [
    path("create", CreateTransactionView.as_view(), name="create_transaction"),
    path("list", TransactionListView.as_view(), name="list_transactions"),
    path("callback", InTouchCallbackView.as_view(), name="intouch-callback"),
]
