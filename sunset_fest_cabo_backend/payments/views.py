from django.shortcuts import render

# Create your views here.
import stripe
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from events.models import Booking
from .models import Payment
from .serializers import PaymentSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY


@api_view(["POST"])
def create_checkout_session(request, booking_id):
    try:
        booking = get_object_or_404(Booking, id=booking_id)

        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Booking for {booking.event_date.event.title}",
                        },
                        "unit_amount": int(
                            booking.total_price * 100
                        ),  # Convert to cents
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=settings.FRONTEND_URL + "/booking/success/",
            cancel_url=settings.FRONTEND_URL + "/booking/cancel/",
            metadata={"booking_id": str(booking.id)},
        )

        # Create payment record
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.total_price,
            currency="USD",
            stripe_session_id=session.id,
            status="pending",
        )

        return Response({"session_id": session.id, "payment_id": payment.id})

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return Response(status=400)
    except stripe.error.SignatureVerificationError as e:
        return Response(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        try:
            payment = Payment.objects.get(stripe_session_id=session.id)
            payment.status = "completed"
            payment.save()

            # Update booking status
            booking = payment.booking
            booking.status = "confirmed"
            booking.is_paid = True
            booking.save()
        except Payment.DoesNotExist:
            return Response(status=404)

    return Response(status=200)


@api_view(["GET"])
def get_booking_by_session(request, session_id):
    try:
        payment = Payment.objects.get(stripe_session_id=session_id)
        booking = payment.booking

        # Serialize the booking with related data
        from events.serializers import BookingSerializer

        serializer = BookingSerializer(booking)

        return Response({"booking": serializer.data})
    except Payment.DoesNotExist:
        return Response({"error": "Payment not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=400)
