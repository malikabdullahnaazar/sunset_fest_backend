# event/admin.py
from django.contrib import admin
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
    AddOnTimeSlot,
    HotelBooking,
    Booking,
    TicketHold,
)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "event_type"]
    search_fields = ["title", "description"]
    list_filter = ["event_type"]


@admin.register(EventDate)
class EventDateAdmin(admin.ModelAdmin):
    list_display = ["title", "event", "date", "city"]
    search_fields = ["title", "city"]
    list_filter = ["event", "date", "city"]
    date_hierarchy = "date"


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "event_date",
        "price",
        "total_tickets",
    ]
    search_fields = ["title", "description"]
    list_filter = ["event_date"]


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(GroupSize)
class GroupSizeAdmin(admin.ModelAdmin):
    list_display = ["pricing_plan", "number_of_persons", "base_price"]
    search_fields = ["pricing_plan__title"]
    list_filter = ["pricing_plan"]


@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    list_display = ["title", "rating", "price", "total_tickets", "available_tickets"]
    search_fields = ["title", "description"]
    list_filter = ["rating"]
    readonly_fields = ["available_tickets"]


@admin.register(AccommodationImage)
class AccommodationImageAdmin(admin.ModelAdmin):
    list_display = ["accommodation", "image"]
    search_fields = ["accommodation__title"]


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1
    fields = ("image",)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "accommodation",
        "bed_type",
        "capacity",
        "total_rooms",
        "get_available_rooms",
        "price",
    )
    list_filter = ("accommodation", "bed_type", "capacity")
    search_fields = ("title", "description", "accommodation__title")
    readonly_fields = ("capacity",)
    fieldsets = (
        (None, {"fields": ("accommodation", "title", "description", "price")}),
        (
            "Room Details",
            {
                "fields": ("bed_type", "total_rooms"),
                "description": "Capacity is automatically calculated based on bed type",
            },
        ),
    )
    inlines = [RoomImageInline]

    def get_available_rooms(self, obj):
        return obj.get_available_rooms()

    get_available_rooms.short_description = "Available Rooms"

    def save_model(self, request, obj, form, change):
        # Update capacity based on bed type when saving
        obj.capacity = obj.get_capacity()
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return ("capacity",)
        return ()  # allow setting capacity when creating new object


@admin.register(RoomImage)
class RoomImageAdmin(admin.ModelAdmin):
    list_display = ["room", "image"]
    search_fields = ["room__title"]


class AddOnTimeSlotInline(admin.TabularInline):
    model = AddOnTimeSlot
    extra = 1
    readonly_fields = ("get_available_capacity",)

    def get_available_capacity(self, obj):
        return obj.get_available_capacity()

    get_available_capacity.short_description = "Available Capacity"


@admin.register(AddOn)
class AddOnAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "event",
        "price",
        "get_available_tickets",
        "min_persons",
        "has_time_slots",
    )
    list_filter = ("event", "has_time_slots")
    search_fields = ("title", "description")
    inlines = [AddOnTimeSlotInline]
    readonly_fields = ("get_available_tickets",)

    def get_available_tickets(self, obj):
        return obj.get_available_tickets()

    get_available_tickets.short_description = "Available Tickets"


@admin.register(HotelBooking)
class HotelBookingAdmin(admin.ModelAdmin):
    list_display = ["accommodation", "check_in_date", "check_out_date"]
    search_fields = ["accommodation__title"]
    list_filter = ["check_in_date", "check_out_date"]
    date_hierarchy = "check_in_date"


@admin.register(TicketHold)
class TicketHoldAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "pricing_plan",
        "number_of_tickets",
        "created_at",
        "expires_at",
    )
    search_fields = ("user__username", "pricing_plan__title")
    list_filter = ("created_at", "expires_at")
    date_hierarchy = "created_at"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "event_date", "status", "total_price", "created_at"]
    search_fields = ["user__username", "event_date__title"]
    list_filter = ["status", "created_at"]
    date_hierarchy = "created_at"
