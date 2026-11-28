from django.urls import path
from apps.billing.views import pay_start
from . import views

urlpatterns = [
    path("ai-lab/wallet/", views.WalletView.as_view(), name="ai-credit-wallet"),
    path("ai-lab/wallet/history/", views.HistoryView.as_view(), name="ai-credit-history"),
    path("ai-lab/wallet/topups/", views.TopUpView.as_view(), name="ai-credit-topup"),
    path("ai-lab/wallet/pay/<str:token>/", pay_start, name="ai-credit-pay-start"),
]
