from django.urls import path

from . import guest, views

urlpatterns = [
    path("billing/catalog/", views.CatalogView.as_view(), name="billing-catalog"),
    path("billing/me/", views.MyAccessView.as_view(), name="billing-me"),
    path("billing/quote/", views.QuoteView.as_view(), name="billing-quote"),
    path("billing/checkout/", views.CheckoutView.as_view(), name="billing-checkout"),
    path("billing/orders/", views.MyOrdersView.as_view(), name="billing-orders"),
    path("billing/callback/", views.payment_callback, name="billing-callback"),
    path("billing/callback/<slug:kind>/", views.payment_callback, name="billing-callback-gateway"),
    path("billing/result/<str:token>/", views.payment_result, name="billing-result"),
    path("guest/status/", guest.GuestStatusView.as_view(), name="guest-status"),
    path("guest/session/", guest.GuestSessionView.as_view(), name="guest-session"),
]
