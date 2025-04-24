from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from django.db import models
from .models import (
    Event,
    EventDate,
    PricingPlan,
    Feature,
    GroupSize,
    Accommodation,
    Room,
    AddOn,
    HotelBooking,
    Booking,
    TicketHold, 
    AddOnTimeSlot,
    RoomHold,
)
from .serializers import (
    EventSerializer,
    EventDateSerializer,
    PricingPlanSerializer,
    FeatureSerializer,
    GroupSizeSerializer,
    AccommodationSerializer,
    RoomSerializer,
    AddOnSerializer,
    HotelBookingSerializer,
    BookingSerializer,
    BookingCreateSerializer,
    AddOnTimeSlotSerializer,
    CombinedHoldSerializer,
)
from django.utils import timezone
import uuid
from datetime import timedelta
from rest_framework.views import APIView


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer


class EventDateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EventDate.objects.all()
    serializer_class = EventDateSerializer

    def get_queryset(self):
        event_id = self.request.query_params.get("event_id")
        if event_id:
            return self.queryset.filter(event_id=event_id)
        return self.queryset


class PricingPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PricingPlan.objects.all()
    serializer_class = PricingPlanSerializer

    def get_queryset(self):
        event_date_id = self.request.query_params.get("event_date_id")
        if event_date_id:
            return self.queryset.filter(event_date_id=event_date_id)
        return self.queryset


class GroupSizeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GroupSize.objects.all()
    serializer_class = GroupSizeSerializer

    def get_queryset(self):
        pricing_plan_id = self.request.query_params.get("pricing_plan_id")
        if pricing_plan_id:
            return self.queryset.filter(pricing_plan_id=pricing_plan_id)
        return self.queryset


class AccommodationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Accommodation.objects.all()
    serializer_class = AccommodationSerializer

    def get_queryset(self):
        pricing_plan_id = self.request.query_params.get("pricing_plan_id")
        if pricing_plan_id:
            return self.queryset.filter(pricing_plan_id=pricing_plan_id)
        return self.queryset


class RoomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

    def get_queryset(self):
        accommodation_id = self.request.query_params.get("accommodation_id")
        if accommodation_id:
            return self.queryset.filter(accommodation_id=accommodation_id)
        return self.queryset


class AddOnViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AddOn.objects.all()
    serializer_class = AddOnSerializer

    def get_queryset(self):
        event_id = self.request.query_params.get("event_id")
        date = self.request.query_params.get("date")

        queryset = self.queryset

        if event_id:
            queryset = queryset.filter(event_id=event_id)

        if date:
            # Filter time slots based on the selected date
            date_obj = timezone.datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.prefetch_related(
                models.Prefetch(
                    "time_slots",
                    queryset=AddOnTimeSlot.objects.filter(
                        start_time__date=date_obj
                    ).order_by("start_time"),
                )
            )
        else:
            queryset = queryset.prefetch_related("time_slots")

        return queryset

    @action(detail=True, methods=["get"])
    def availability(self, request, pk=None):
        addon = self.get_object()
        date = request.query_params.get("date")

        if not date:
            return Response(
                {"error": "Date parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            date_obj = timezone.datetime.strptime(date, "%Y-%m-%d").date()
            time_slots = addon.time_slots.filter(start_time__date=date_obj).order_by(
                "start_time"
            )

            return Response(
                {
                    "available_tickets": addon.get_available_tickets(),
                    "time_slots": AddOnTimeSlotSerializer(time_slots, many=True).data,
                }
            )
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class AddOnTimeSlotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AddOnTimeSlot.objects.all()
    serializer_class = AddOnTimeSlotSerializer

    def get_queryset(self):
        addon_id = self.request.query_params.get("addon_id")
        if addon_id:
            return self.queryset.filter(add_on_id=addon_id)
        return self.queryset

    @action(detail=True, methods=["get"])
    def availability(self, request, pk=None):
        time_slot = self.get_object()
        available_capacity = time_slot.get_available_capacity()
        return Response(
            {
                "available_capacity": available_capacity,
                "total_capacity": time_slot.total_capacity,
                "start_time": time_slot.start_time,
                "end_time": time_slot.end_time,
            }
        )


class HotelBookingViewSet(viewsets.ModelViewSet):
    queryset = HotelBooking.objects.all()
    serializer_class = HotelBookingSerializer

    def perform_create(self, serializer):
        serializer.save()


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingCreateSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(["GET"])
def get_addon_availability(request, event_id, addon_id):
    try:
        addon = AddOn.objects.get(id=addon_id, event_id=event_id)
        available_tickets = addon.get_available_tickets()
        return Response({"available_tickets": available_tickets})
    except AddOn.DoesNotExist:
        return Response({"error": "Add-on not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
def get_time_slot_availability(request, addon_id, time_slot_id):
    try:
        event_id = request.query_params.get("event_id")
        if not event_id:
            return Response(
                {"error": "Event ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        time_slot = AddOnTimeSlot.objects.get(
            id=time_slot_id, add_on_id=addon_id, add_on__event_id=event_id
        )
        available_capacity = time_slot.get_available_capacity()
        return Response({"available_capacity": available_capacity})
    except AddOnTimeSlot.DoesNotExist:
        return Response(
            {"error": "Time slot not found"}, status=status.HTTP_404_NOT_FOUND
        )


class CombinedHoldView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CombinedHoldSerializer(data=request.data)
        if serializer.is_valid():
            pricing_plan = serializer.validated_data["pricing_plan"]
            number_of_tickets = serializer.validated_data["number_of_tickets"]
            room_holds_data = serializer.validated_data.get("room_holds", [])

            # Generate session ID for unauthenticated users
            session_id = None
            if not request.user.is_authenticated:
                session_id = request.session.get("session_id")
                if not session_id:
                    session_id = str(uuid.uuid4())
                    request.session["session_id"] = session_id

            # Create ticket hold
            expires_at = timezone.now() + timedelta(minutes=5)
            ticket_hold = TicketHold.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_id=session_id,
                pricing_plan=pricing_plan,
                number_of_tickets=number_of_tickets,
                expires_at=expires_at,
            )

            # Create room holds if provided
            room_holds = []
            for room_data in room_holds_data:
                room = Room.objects.get(id=room_data["room_id"])
                room_hold = RoomHold.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    session_id=session_id,
                    room=room,
                    quantity=room_data["quantity"],
                    expires_at=expires_at,
                )
                room_holds.append(room_hold)
                ticket_hold.room_holds.add(room_hold)

            # Return the created holds
            return Response(
                {
                    "ticket_hold": TicketHoldSerializer(ticket_hold).data,
                    "room_holds": RoomHoldSerializer(room_holds, many=True).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
