from django.urls import path

from . import views

urlpatterns = [
    path("billing/catalog/", views.CatalogView.as_view(), name="billing-catalog"),
    path("billing/me/", views.MyAccessView.as_view(), name="billing-me"),
    path("billing/quote/", views.QuoteView.as_view(), name="billing-quote"),
    path("billing/checkout/", views.CheckoutView.as_view(), name="billing-checkout"),
    path("billing/orders/", views.MyOrdersView.as_view(), name="billing-orders"),
    path("billing/callback/", views.payment_callback, name="billing-callback"),
]
