# event/admin.py
from django.contrib import admin
from .models import (
    Event, EventDate, PricingPlan, Feature, GroupSize,
    Accommodation, AccommodationImage, Room, RoomImage,
    AddOn, HotelBooking, Booking
)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type']
    search_fields = ['title', 'description']
    list_filter = ['event_type']

@admin.register(EventDate)
class EventDateAdmin(admin.ModelAdmin):
    list_display = ['title', 'event', 'date', 'city']
    search_fields = ['title', 'city']
    list_filter = ['event', 'date', 'city']
    date_hierarchy = 'date'

@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_date', 'price', 'total_tickets', 'available_tickets']
    search_fields = ['title', 'description']
    list_filter = ['event_date']
    readonly_fields = ['available_tickets']

@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(GroupSize)
class GroupSizeAdmin(admin.ModelAdmin):
    list_display = ['pricing_plan', 'number_of_persons', 'base_price']
    search_fields = ['pricing_plan__title']
    list_filter = ['pricing_plan']

@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    list_display = ['title', 'rating', 'price', 'total_tickets', 'available_tickets']
    search_fields = ['title', 'description']
    list_filter = ['rating']
    readonly_fields = ['available_tickets']

@admin.register(AccommodationImage)
class AccommodationImageAdmin(admin.ModelAdmin):
    list_display = ['accommodation', 'image']
    search_fields = ['accommodation__title']

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['title', 'accommodation', 'price', 'total_tickets', 'available_tickets']
    search_fields = ['title', 'description']
    list_filter = ['accommodation']
    readonly_fields = ['available_tickets']

@admin.register(RoomImage)
class RoomImageAdmin(admin.ModelAdmin):
    list_display = ['room', 'image']
    search_fields = ['room__title']

@admin.register(AddOn)
class AddOnAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'total_tickets', 'available_tickets']
    search_fields = ['title', 'description']
    readonly_fields = ['available_tickets']

@admin.register(HotelBooking)
class HotelBookingAdmin(admin.ModelAdmin):
    list_display = ['accommodation', 'check_in_date', 'check_out_date']
    search_fields = ['accommodation__title']
    list_filter = ['check_in_date', 'check_out_date']
    date_hierarchy = 'check_in_date'

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'event_date', 'status', 'total_price', 'created_at']
    search_fields = ['user__username', 'event_date__title']
    list_filter = ['status', 'created_at']
    date_hierarchy = 'created_at'