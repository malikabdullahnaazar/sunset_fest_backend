# event/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EventViewSet,
    EventDateViewSet,
    PricingPlanViewSet,
    GroupSizeViewSet,
    AccommodationViewSet,
    RoomViewSet,
    AddOnViewSet,
    AddOnTimeSlotViewSet,
    BookingViewSet,
    TicketHoldViewSet,
    RoomHoldViewSet,
    CombinedHoldView,
    get_addon_availability,
    get_time_slot_availability,
)

router = DefaultRouter()
router.register(r"events", EventViewSet)
router.register(r"event-dates", EventDateViewSet)
router.register(r"pricing-plans", PricingPlanViewSet)
router.register(r"group-sizes", GroupSizeViewSet)
router.register(r"accommodations", AccommodationViewSet)
router.register(r"rooms", RoomViewSet)
router.register(r"add-ons", AddOnViewSet)
router.register(r"add-on-time-slots", AddOnTimeSlotViewSet)
router.register(r"bookings", BookingViewSet)
router.register(r"ticket-holds", TicketHoldViewSet)
router.register(r"room-holds", RoomHoldViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "add-ons/<uuid:addon_id>/availability/",
        get_addon_availability,
        name="addon-availability",
    ),
    path(
        "add-ons/<uuid:addon_id>/time-slots/<uuid:time_slot_id>/availability/",
        get_time_slot_availability,
        name="time-slot-availability",
    ),
    path("combined-hold/", CombinedHoldView.as_view(), name="combined-hold"),
]
