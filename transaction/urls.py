from django.urls import path

from .views.intouch_callback import InTouchCallbackView
from .views.transaction import TransactionView
from .views.transaction_detail import TransactionDetailView

urlpatterns = [
    path("", TransactionView.as_view(), name="create_transaction"),
    path("transactions/<uuid:uuid>/", TransactionDetailView.as_view(), name="transaction-detail"),
    path("callback", InTouchCallbackView.as_view(), name="intouch-callback"),
]
