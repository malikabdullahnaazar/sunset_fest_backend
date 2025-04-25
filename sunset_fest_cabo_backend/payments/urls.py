from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path(
        "checkout-session/<uuid:booking_id>/",
        views.create_checkout_session,
        name="create-checkout-session",
    ),
    path("webhook/", views.stripe_webhook, name="stripe-webhook"),
    path(
        "session/<str:session_id>/",
        views.get_booking_by_session,
        name="get-booking-by-session",
    ),
]
