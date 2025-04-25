from rest_framework import serializers
from .models import (
    Event,
    EventDate,
    PricingPlan,
    Feature,
    GroupSize,
    Accommodation,
    AccommodationImage,
    Room,
    RoomImage,
    AddOn,
    HotelBooking,
    Booking,
    TicketHold,
    AddOnTimeSlot,
    BookingAddOn,
    RoomHold,
    BookingRoom,
)
from django.utils import timezone
from datetime import timedelta


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ["id", "name"]


class PricingPlanSerializer(serializers.ModelSerializer):
    feature = FeatureSerializer(many=True, read_only=True)
    available_tickets = serializers.SerializerMethodField()

    class Meta:
        model = PricingPlan
        fields = [
            "id",
            "title",
            "description",
            "price",
            "banner_image",
            "feature",
            "total_tickets",
            "available_tickets",
        ]

    def get_available_tickets(self, obj):
        return obj.get_available_tickets()


class GroupSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupSize
        fields = ["id", "number_of_persons", "base_price"]


class EventDateSerializer(serializers.ModelSerializer):
    pricing_plans = PricingPlanSerializer(many=True, read_only=True)

    class Meta:
        model = EventDate
        fields = ["id", "date", "city", "title", "description", "pricing_plans"]


class EventSerializer(serializers.ModelSerializer):
    dates = EventDateSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = ["id", "title", "description", "event_type", "dates", "image"]


class AccommodationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccommodationImage
        fields = ["id", "image"]


class AccommodationSerializer(serializers.ModelSerializer):
    images = AccommodationImageSerializer(many=True, read_only=True)

    class Meta:
        model = Accommodation
        fields = [
            "id",
            "title",
            "description",
            "rating",
            "price",
            "images",
            "total_tickets",
            "available_tickets",
        ]


class RoomImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomImage
        fields = ["id", "image"]


class RoomSerializer(serializers.ModelSerializer):
    images = RoomImageSerializer(many=True, read_only=True)
    accommodation = AccommodationSerializer(read_only=True)
    available_rooms = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = [
            "id",
            "title",
            "description",
            "price",
            "bed_type",
            "capacity",
            "total_rooms",
            "available_rooms",
            "images",
            "accommodation",
        ]
        read_only_fields = ["capacity", "available_rooms"]

    def get_available_rooms(self, obj):
        return obj.get_available_rooms()


class AddOnTimeSlotSerializer(serializers.ModelSerializer):
    available_capacity = serializers.SerializerMethodField()

    class Meta:
        model = AddOnTimeSlot
        fields = [
            "id",
            "start_time",
            "end_time",
            "total_capacity",
            "available_capacity",
            "price_override",
        ]

    def get_available_capacity(self, obj):
        return obj.get_available_capacity()


class AddOnSerializer(serializers.ModelSerializer):
    time_slots = AddOnTimeSlotSerializer(many=True, read_only=True)
    available_tickets = serializers.SerializerMethodField()

    class Meta:
        model = AddOn
        fields = [
            "id",
            "title",
            "description",
            "price",
            "image",
            "total_tickets",
            "available_tickets",
            "event",
            "min_persons",
            "has_time_slots",
            "time_slots",
        ]

    def get_available_tickets(self, obj):
        return obj.get_available_tickets()


class BookingAddOnSerializer(serializers.ModelSerializer):
    add_on = AddOnSerializer(read_only=True)
    time_slot = AddOnTimeSlotSerializer(read_only=True)

    class Meta:
        model = BookingAddOn
        fields = [
            "id",
            "add_on",
            "time_slot",
            "quantity",
            "price",
            "created_at",
        ]


class BookingAddOnCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingAddOn
        fields = [
            "add_on",
            "time_slot",
            "quantity",
        ]

    def validate(self, data):
        add_on = data["add_on"]
        time_slot = data.get("time_slot")
        quantity = data["quantity"]

        if add_on.has_time_slots and not time_slot:
            raise serializers.ValidationError("Time slot is required for this add-on")

        if time_slot and time_slot.add_on != add_on:
            raise serializers.ValidationError(
                "Time slot must belong to the selected add-on"
            )

        if time_slot:
            if time_slot.available_capacity < quantity:
                raise serializers.ValidationError(
                    f"Not enough capacity available for the selected time slot"
                )
        else:
            if add_on.available_tickets < quantity:
                raise serializers.ValidationError(
                    f"Not enough tickets available for add-on {add_on.title}"
                )

        return data


class HotelBookingSerializer(serializers.ModelSerializer):
    accommodation = AccommodationSerializer(read_only=True)
    accommodation_id = serializers.PrimaryKeyRelatedField(
        queryset=Accommodation.objects.all(), source="accommodation", write_only=True
    )

    class Meta:
        model = HotelBooking
        fields = [
            "id",
            "accommodation",
            "accommodation_id",
            "check_in_date",
            "check_out_date",
            "checkin_first_name",
            "checkin_last_name",
            "checkin_email",
        ]


class BookingRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingRoom
        fields = ["room", "quantity", "price"]


class BookingRoomCreateSerializer(serializers.ModelSerializer):
    room_id = serializers.UUIDField(write_only=True)
    room = RoomSerializer(read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    class Meta:
        model = BookingRoom
        fields = ["room_id", "room", "quantity", "price"]

    def validate(self, data):
        room_id = data.pop("room_id")
        try:
            room = Room.objects.get(id=room_id)
            data["room"] = room
            # Set price from room if not provided
            if "price" not in data:
                data["price"] = room.price
        except Room.DoesNotExist:
            raise serializers.ValidationError(f"Room with id {room_id} does not exist")
        return data


class BookingCreateSerializer(serializers.ModelSerializer):
    rooms = BookingRoomCreateSerializer(many=True, required=False)
    user_email = serializers.EmailField(required=False)
    hotel_booking = HotelBookingSerializer(required=False)

    class Meta:
        model = Booking
        fields = [
            "id",
            "event_date",
            "pricing_plan",
            "group_size",
            "hotel_booking",
            "rooms",
            "add_ons",
            "user_email",
            "ticket_hold_id",
        ]

    def create(self, validated_data):
        rooms_data = validated_data.pop("rooms", [])
        hotel_booking = validated_data.pop("hotel_booking", None)
        add_ons = validated_data.pop("add_ons", [])

        # Remove status if it exists in validated_data
        validated_data.pop("status", None)

        # Create booking
        booking = Booking.objects.create(
            **validated_data, hotel_booking=hotel_booking, status="CONFIRMED"
        )

        # Set add-ons
        booking.add_ons.set(add_ons)

        # Create booking rooms
        for room_data in rooms_data:
            BookingRoom.objects.create(booking=booking, **room_data)

        return booking


class CombinedHoldSerializer(serializers.Serializer):
    pricing_plan_id = serializers.PrimaryKeyRelatedField(
        queryset=PricingPlan.objects.all(), source="pricing_plan"
    )
    number_of_tickets = serializers.IntegerField(min_value=1)
    room_holds = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField(), allow_empty=False),
        required=False,
    )

    def validate(self, data):
        pricing_plan = data["pricing_plan"]
        number_of_tickets = data["number_of_tickets"]
        room_holds = data.get("room_holds", [])

        # Validate ticket availability
        if pricing_plan.get_available_tickets() < number_of_tickets:
            raise serializers.ValidationError(
                f"Not enough tickets available for pricing plan {pricing_plan.title}"
            )

        # Validate room availability
        for room_hold in room_holds:
            room_id = room_hold.get("room_id")
            quantity = room_hold.get("quantity")
            if not room_id or not quantity:
                raise serializers.ValidationError(
                    "Each room hold must have room_id and quantity"
                )

            try:
                room = Room.objects.get(id=room_id)
                if room.get_available_rooms() < int(quantity):
                    raise serializers.ValidationError(
                        f"Not enough rooms available for {room.title}"
                    )
            except Room.DoesNotExist:
                raise serializers.ValidationError(
                    f"Room with id {room_id} does not exist"
                )
            except ValueError:
                raise serializers.ValidationError(f"Quantity must be a valid number")

        return data


class BookingSerializer(serializers.ModelSerializer):
    event_date = EventDateSerializer(read_only=True)
    pricing_plan = PricingPlanSerializer(read_only=True)
    group_size = GroupSizeSerializer(read_only=True)
    hotel_booking = HotelBookingSerializer(read_only=True)
    rooms = BookingRoomSerializer(many=True, read_only=True)
    add_ons = AddOnSerializer(many=True, read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "event_date",
            "pricing_plan",
            "group_size",
            "hotel_booking",
            "rooms",
            "add_ons",
            "total_price",
            "status",
            "is_paid",
            "created_at",
            "updated_at",
        ]
