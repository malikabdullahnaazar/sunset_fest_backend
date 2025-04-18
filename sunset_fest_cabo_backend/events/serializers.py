# event/serializers.py
from rest_framework import serializers
from .models import (
    Event, EventDate, PricingPlan, Feature, GroupSize,
    Accommodation, AccommodationImage, Room, RoomImage,
    AddOn, HotelBooking, Booking
)

class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ['id', 'name']

class PricingPlanSerializer(serializers.ModelSerializer):
    features = FeatureSerializer(many=True, read_only=True)
    
    class Meta:
        model = PricingPlan
        fields = ['id', 'title', 'description', 'price', 'banner_image', 'features', 'total_tickets', 'available_tickets']

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
        fields = ['id', 'title', 'description', 'event_type', 'dates']

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
    
    class Meta:
        model = Room
        fields = ['id', 'title', 'description', 'price', 'images', 'total_tickets', 'available_tickets']

class AddOnSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddOn
        fields = ['id', 'title', 'description', 'price', 'image', 'total_tickets', 'available_tickets']

class HotelBookingSerializer(serializers.ModelSerializer):
    accommodation = AccommodationSerializer(read_only=True)
    accommodation_id = serializers.PrimaryKeyRelatedField(
        queryset=Accommodation.objects.all(), source='accommodation', write_only=True
    )
    
    class Meta:
        model = HotelBooking
        fields = ['id', 'accommodation', 'accommodation_id', 'check_in_date', 'check_out_date']

class BookingSerializer(serializers.ModelSerializer):
    event_date = EventDateSerializer(read_only=True)
    pricing_plan = PricingPlanSerializer(read_only=True)
    group_size = GroupSizeSerializer(read_only=True)
    hotel_booking = HotelBookingSerializer(read_only=True)
    room = RoomSerializer(read_only=True)
    add_ons = AddOnSerializer(many=True, read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'event_date', 'pricing_plan', 'group_size',
            'hotel_booking', 'room', 'add_ons', 'total_price',
            'status', 'created_at', 'updated_at'
        ]

class BookingCreateSerializer(serializers.ModelSerializer):
    add_ons = serializers.PrimaryKeyRelatedField(many=True, queryset=AddOn.objects.all())
    hotel_booking = HotelBookingSerializer(required=False)
    room_id = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all(), source='room', required=False, allow_null=True
    )
    
    class Meta:
        model = Booking
        fields = [
            'event_date', 'pricing_plan', 'group_size',
            'hotel_booking', 'room_id', 'add_ons'
        ]
    
    def validate(self, data):
        # Ensure all related objects belong to the correct hierarchy
        event_date = data['event_date']
        pricing_plan = data['pricing_plan']
        group_size = data['group_size']
        
        if pricing_plan.event_date != event_date:
            raise serializers.ValidationError("Pricing plan does not belong to the selected event date")
        
        if group_size.pricing_plan != pricing_plan:
            raise serializers.ValidationError("Group size does not belong to the selected pricing plan")
        
        if data.get('room') and data.get('hotel_booking'):
            if data['room'].accommodation != data['hotel_booking']['accommodation']:
                raise serializers.ValidationError("Room must belong to the selected accommodation")
        
        # Validate ticket availability
        tickets_needed = group_size.number_of_persons
        if pricing_plan.available_tickets < tickets_needed:
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
        
        # Create hotel booking if provided
        hotel_booking = None
        if hotel_booking_data:
            hotel_booking = HotelBooking.objects.create(**hotel_booking_data)
        
        booking = Booking.objects.create(
            user=self.context['request'].user,
            hotel_booking=hotel_booking,
            **validated_data
        )
        booking.add_ons.set(add_ons)
        return booking