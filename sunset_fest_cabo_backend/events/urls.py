# event/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EventViewSet, EventDateViewSet, PricingPlanViewSet,
    GroupSizeViewSet, AccommodationViewSet, RoomViewSet,
    AddOnViewSet, HotelBookingViewSet, BookingViewSet
)

router = DefaultRouter()
router.register(r'events', EventViewSet)
router.register(r'event-dates', EventDateViewSet)
router.register(r'pricing-plans', PricingPlanViewSet)
router.register(r'group-sizes', GroupSizeViewSet)
router.register(r'accommodations', AccommodationViewSet)
router.register(r'rooms', RoomViewSet)
router.register(r'add-ons', AddOnViewSet)
router.register(r'hotel-bookings', HotelBookingViewSet)
router.register(r'bookings', BookingViewSet)

urlpatterns = [
    path('', include(router.urls)),
]