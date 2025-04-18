from rest_framework import serializers
from .models import (
    Event, EventDate, PricingPlan, Feature, GroupSize,
    Accommodation, AccommodationImage, Room, RoomImage,
    AddOn, HotelBooking, Booking, TicketHold
)
from django.utils import timezone

class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ['id', 'name']

class PricingPlanSerializer(serializers.ModelSerializer):
    feature = FeatureSerializer(many=True, read_only=True)
    available_tickets = serializers.SerializerMethodField()
    
    class Meta:
        model = PricingPlan
        fields = ['id', 'title', 'description', 'price', 'banner_image', 'feature', 'total_tickets', 'available_tickets']
    
    def get_available_tickets(self, obj):
        return obj.get_available_tickets()

class GroupSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupSize
        fields = ['id', 'number_of_persons', 'base_price']

class EventDateSerializer(serializers.ModelSerializer):
    pricing_plans = PricingPlanSerializer(many=True, read_only=True)
    
    class Meta:
        model = EventDate
        fields = ['id', 'date', 'city', 'title', 'description', 'pricing_plans']

class EventSerializer(serializers.ModelSerializer):
    dates = EventDateSerializer(many=True, read_only=True)
    
    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'event_type', 'dates', 'image']

class AccommodationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccommodationImage
        fields = ['id', 'image']

class AccommodationSerializer(serializers.ModelSerializer):
    images = AccommodationImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Accommodation
        fields = ['id', 'title', 'description', 'rating', 'price', 'images', 'total_tickets', 'available_tickets']

class RoomImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomImage
        fields = ['id', 'image']

class RoomSerializer(serializers.ModelSerializer):
    images = RoomImageSerializer(many=True, read_only=True)
    accommodation = AccommodationSerializer(read_only=True)
    
    class Meta:
        model = Room
        fields = ['id', 'title', 'description', 'price', 'images', 'total_tickets', 'available_tickets', 'accommodation', 'bed_type']

class AddOnSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddOn
        fields = ['id', 'title', 'description', 'price', 'image', 'total_tickets', 'available_tickets', 'event']

class HotelBookingSerializer(serializers.ModelSerializer):
    accommodation = AccommodationSerializer(read_only=True)
    accommodation_id = serializers.PrimaryKeyRelatedField(
        queryset=Accommodation.objects.all(), source='accommodation', write_only=True
    )
    
    class Meta:
        model = HotelBooking
        fields = ['id', 'accommodation', 'accommodation_id', 'check_in_date', 'check_out_date']

class TicketHoldSerializer(serializers.ModelSerializer):
    pricing_plan = PricingPlanSerializer(read_only=True)
    pricing_plan_id = serializers.PrimaryKeyRelatedField(
        queryset=PricingPlan.objects.all(), source='pricing_plan', write_only=True
    )
    
    class Meta:
        model = TicketHold
        fields = ['id', 'pricing_plan', 'pricing_plan_id', 'number_of_tickets', 'created_at', 'expires_at']
    
    def validate(self, data):
        tickets_needed = data['number_of_tickets']
        pricing_plan = data['pricing_plan']
        
        if pricing_plan.get_available_tickets() < tickets_needed:
            raise serializers.ValidationError(
                f"Not enough tickets available for pricing plan {pricing_plan.title}"
            )
        
        return data

class BookingSerializer(serializers.ModelSerializer):
    event_date = EventDateSerializer(read_only=True)
    pricing_plan = PricingPlanSerializer(read_only=True)
    group_size = GroupSizeSerializer(read_only=True)
    hotel_booking = HotelBookingSerializer(read_only=True)
    room = RoomSerializer(read_only=True)
    add_ons = AddOnSerializer(many=True, read_only=True)
    ticket_hold = TicketHoldSerializer(read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'event_date', 'pricing_plan', 'group_size',
            'hotel_booking', 'room', 'add_ons', 'ticket_hold',
            'total_price', 'status', 'created_at', 'updated_at'
        ]

class BookingCreateSerializer(serializers.ModelSerializer):
    add_ons = serializers.PrimaryKeyRelatedField(many=True, queryset=AddOn.objects.all())
    hotel_booking = HotelBookingSerializer(required=False)
    room_id = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all(), source='room', required=False, allow_null=True
    )
    ticket_hold_id = serializers.PrimaryKeyRelatedField(
        queryset=TicketHold.objects.all(), source='ticket_hold', required=False, allow_null=True
    )
    
    class Meta:
        model = Booking
        fields = [
            'event_date', 'pricing_plan', 'group_size',
            'hotel_booking', 'room_id', 'add_ons', 'ticket_hold_id'
        ]
    
    def validate(self, data):
        event_date = data['event_date']
        pricing_plan = data['pricing_plan']
        group_size = data['group_size']
        ticket_hold = data.get('ticket_hold')
        
        if pricing_plan.event_date != event_date:
            raise serializers.ValidationError("Pricing plan does not belong to the selected event date")
        
        if group_size.pricing_plan != pricing_plan:
            raise serializers.ValidationError("Group size does not belong to the selected pricing plan")
        
        if data.get('room') and data.get('hotel_booking'):
            if data['room'].accommodation != data['hotel_booking']['accommodation']:
                raise serializers.ValidationError("Room must belong to the selected accommodation")
        
        tickets_needed = group_size.number_of_persons
        
        # Validate ticket hold if provided
        if ticket_hold:
            if ticket_hold.pricing_plan != pricing_plan:
                raise serializers.ValidationError("Ticket hold does not belong to the selected pricing plan")
            if ticket_hold.number_of_tickets < tickets_needed:
                raise serializers.ValidationError("Ticket hold does not cover enough tickets")
            if ticket_hold.expires_at < timezone.now():
                raise serializers.ValidationError("Ticket hold has expired")
        
        # Validate ticket availability
        if pricing_plan.get_available_tickets() < tickets_needed:
            raise serializers.ValidationError(
                f"Not enough tickets available for pricing plan {pricing_plan.title}"
            )
        
        if data.get('hotel_booking'):
            accommodation = data['hotel_booking']['accommodation']
            if accommodation.available_tickets < tickets_needed:
                raise serializers.ValidationError(
                    f"Not enough tickets available for accommodation {accommodation.title}"
                )
        
        if data.get('room') and data['room'].available_tickets < tickets_needed:
            raise serializers.ValidationError(
                f"Not enough tickets available for room {data['room'].title}"
            )
        
        for add_on in data.get('add_ons', []):
            if add_on.available_tickets < tickets_needed:
                raise serializers.ValidationError(
                    f"Not enough tickets available for add-on {add_on.title}"
                )
        
        return data
    
    def create(self, validated_data):
        add_ons = validated_data.pop('add_ons', [])
        hotel_booking_data = validated_data.pop('hotel_booking', None)
        
        hotel_booking = None
        if hotel_booking_data:
            hotel_booking = HotelBooking.objects.create(**hotel_booking_data)
        
        booking = Booking.objects.create(
            user=self.context['request'].user,
            hotel_booking=hotel_booking,
            **validated_data
        )
        booking.add_ons.set(add_ons)
        booking.status = 'CONFIRMED'
        booking.save()
        return booking