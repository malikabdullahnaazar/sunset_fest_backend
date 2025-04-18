# event/views.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import (
    Event, EventDate, PricingPlan, Feature, GroupSize,
    Accommodation, Room, AddOn, HotelBooking, Booking
)
from .serializers import (
    EventSerializer, EventDateSerializer, PricingPlanSerializer,
    FeatureSerializer, GroupSizeSerializer, AccommodationSerializer,
    RoomSerializer, AddOnSerializer, HotelBookingSerializer,
    BookingSerializer, BookingCreateSerializer
)

class EventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

class EventDateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EventDate.objects.all()
    serializer_class = EventDateSerializer
    
    def get_queryset(self):
        event_id = self.request.query_params.get('event_id')
        if event_id:
            return self.queryset.filter(event_id=event_id)
        return self.queryset

class PricingPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PricingPlan.objects.all()
    serializer_class = PricingPlanSerializer
    
    def get_queryset(self):
        event_date_id = self.request.query_params.get('event_date_id')
        if event_date_id:
            return self.queryset.filter(event_date_id=event_date_id)
        return self.queryset

class GroupSizeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GroupSize.objects.all()
    serializer_class = GroupSizeSerializer
    
    def get_queryset(self):
        pricing_plan_id = self.request.query_params.get('pricing_plan_id')
        if pricing_plan_id:
            return self.queryset.filter(pricing_plan_id=pricing_plan_id)
        return self.queryset

class AccommodationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Accommodation.objects.all()
    serializer_class = AccommodationSerializer

class RoomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    
    def get_queryset(self):
        accommodation_id = self.request.query_params.get('accommodation_id')
        if accommodation_id:
            return self.queryset.filter(accommodation_id=accommodation_id)
        return self.queryset

class AddOnViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AddOn.objects.all()
    serializer_class = AddOnSerializer

class HotelBookingViewSet(viewsets.ModelViewSet):
    queryset = HotelBooking.objects.all()
    serializer_class = HotelBookingSerializer
    
    def perform_create(self, serializer):
        serializer.save()

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingSerializer
    
    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)