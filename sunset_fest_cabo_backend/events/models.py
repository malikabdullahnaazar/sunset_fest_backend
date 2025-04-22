from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
from django.contrib.auth import get_user_model
from datetime import timedelta


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=100)
    image = models.ImageField(upload_to="events/")

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class EventDate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="dates")
    date = models.DateTimeField()
    city = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    description = models.TextField()

    class Meta:
        ordering = ["date"]
        unique_together = ["event", "date", "city"]

    def __str__(self):
        return f"{self.title} - {self.city} ({self.date})"


class Feature(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class PricingPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_date = models.ForeignKey(
        EventDate, on_delete=models.CASCADE, related_name="pricing_plans"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    banner_image = models.ImageField(
        upload_to="pricing_banners/", null=True, blank=True
    )
    feature = models.ManyToManyField(Feature, related_name="features")
    total_tickets = models.PositiveIntegerField(default=0)

    def clean(self):
        pass  # Removed available_tickets validation as it's now dynamic

    def get_available_tickets(self):
        # Calculate tickets used by confirmed bookings
        confirmed_bookings = Booking.objects.filter(
            pricing_plan=self, status="CONFIRMED"
        )
        tickets_used = sum(
            booking.group_size.number_of_persons for booking in confirmed_bookings
        )

        # Calculate tickets currently held
        active_holds = TicketHold.objects.filter(
            pricing_plan__event_date__event=self.event_date.event,
            expires_at__gt=timezone.now(),
        )
        held_tickets = sum(hold.number_of_tickets for hold in active_holds)

        return self.total_tickets - tickets_used - held_tickets

    def __str__(self):
        return f"{self.title} - {self.event_date.title}"


class GroupSize(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pricing_plan = models.ForeignKey(
        PricingPlan, on_delete=models.CASCADE, related_name="group_sizes"
    )
    number_of_persons = models.PositiveIntegerField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ["pricing_plan", "number_of_persons"]

    def __str__(self):
        return f"{self.number_of_persons} persons - {self.pricing_plan.title}"


class Accommodation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pricing_plan = models.ForeignKey(
        PricingPlan,
        on_delete=models.CASCADE,
        related_name="event",
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    rating = models.FloatField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_tickets = models.PositiveIntegerField(default=0)
    available_tickets = models.PositiveIntegerField(default=0)

    def clean(self):
        if self.available_tickets > self.total_tickets:
            raise ValidationError("Available tickets cannot exceed total tickets")

    def __str__(self):
        return self.title


class AccommodationImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accommodation = models.ForeignKey(
        Accommodation, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="accommodation_images/")

    def __str__(self):
        return f"Image for {self.accommodation.title}"


class Room(models.Model):
    BED_TYPE_CHOICES = [
        ("single", "Single Bed"),
        ("double", "Double Bed"),
        ("queen", "Queen Bed"),
        ("king", "King Bed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accommodation = models.ForeignKey(
        Accommodation, on_delete=models.CASCADE, related_name="rooms"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    bed_type = models.CharField(
        max_length=50, choices=BED_TYPE_CHOICES, default="double"
    )
    capacity = models.PositiveIntegerField(
        default=2, help_text="Number of people the room can accommodate"
    )
    total_rooms = models.PositiveIntegerField(
        default=0, help_text="Total number of rooms available"
    )

    def clean(self):
        if self.total_rooms < 0:
            raise ValidationError("Total rooms cannot be negative")

    def get_capacity(self):
        # Return capacity based on bed type
        if self.bed_type == "single":
            return 1
        elif self.bed_type in ["double", "queen"]:
            return 2
        elif self.bed_type == "king":
            return 2  # or 4 if it's a king suite
        return 2  # default

    def get_available_rooms(self):
        # Get all confirmed bookings for this room type
        confirmed_bookings = Booking.objects.filter(
            room=self, status="CONFIRMED"
        ).count()

        # Get all active room holds
        active_room_holds = RoomHold.objects.filter(
            room=self, expires_at__gt=timezone.now()
        )
        held_rooms = sum(hold.quantity for hold in active_room_holds)

        # Calculate available rooms
        available = self.total_rooms - confirmed_bookings - held_rooms

        # Ensure we don't return negative availability
        return max(0, available)

    def can_accommodate_group(self, group_size, selected_rooms=None):
        """
        Check if this room can accommodate a group of the given size.
        Returns the number of rooms needed to accommodate the group.

        Args:
            group_size: Total number of people in the group
            selected_rooms: List of already selected rooms and their quantities
        """
        if group_size <= 0:
            return 0

        # Calculate how many rooms of this type are needed
        rooms_needed = (
            group_size + self.capacity - 1
        ) // self.capacity  # Ceiling division

        # If we have selected rooms, subtract their capacity from the group size
        if selected_rooms:
            remaining_people = group_size
            for room, quantity in selected_rooms:
                if room.id != self.id:  # Only subtract capacity from other rooms
                    remaining_people = max(
                        0, remaining_people - (room.capacity * quantity)
                    )

            # Recalculate rooms needed for remaining people
            rooms_needed = (remaining_people + self.capacity - 1) // self.capacity

        # Check if we have enough available rooms
        available_rooms = self.get_available_rooms()

        # If this room type is already selected, subtract those from available rooms
        if selected_rooms:
            for room, quantity in selected_rooms:
                if room.id == self.id:
                    available_rooms -= quantity

        return rooms_needed if rooms_needed <= available_rooms else 0

    def save(self, *args, **kwargs):
        # Update capacity based on bed type when saving
        self.capacity = self.get_capacity()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.accommodation.title}"


class RoomImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="room_images/")

    def __str__(self):
        return f"Image for {self.room.title}"


class AddOn(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="AddOn", blank=True, null=True
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="addon_images/", null=True, blank=True)
    total_tickets = models.PositiveIntegerField(default=0)
    min_persons = models.PositiveIntegerField(default=1)
    has_time_slots = models.BooleanField(default=False)

    def get_available_tickets(self):
        # Calculate tickets used by confirmed bookings
        confirmed_bookings = Booking.objects.filter(add_ons=self, status="CONFIRMED")
        tickets_used = sum(
            booking.group_size.number_of_persons for booking in confirmed_bookings
        )

        # Calculate tickets currently held
        active_holds = TicketHold.objects.filter(
            pricing_plan__event_date__event=self.event, expires_at__gt=timezone.now()
        )
        held_tickets = sum(hold.number_of_tickets for hold in active_holds)

        return self.total_tickets - tickets_used - held_tickets

    def __str__(self):
        return self.title


class AddOnTimeSlot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    add_on = models.ForeignKey(
        AddOn, on_delete=models.CASCADE, related_name="time_slots"
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    total_capacity = models.PositiveIntegerField(default=0)
    price_override = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    class Meta:
        ordering = ["start_time"]

    def clean(self):
        if self.end_time and self.start_time > self.end_time:
            raise ValidationError("End time must be after start time")

    def get_available_capacity(self):
        # Calculate capacity used by confirmed bookings
        confirmed_bookings = BookingAddOn.objects.filter(
            time_slot=self, booking__status="CONFIRMED"
        )
        capacity_used = sum(booking.quantity for booking in confirmed_bookings)

        # Calculate capacity currently held
        active_holds = TicketHold.objects.filter(
            pricing_plan__event_date__event=self.add_on.event,
            expires_at__gt=timezone.now(),
        )
        held_capacity = sum(hold.number_of_tickets for hold in active_holds)

        return self.total_capacity - capacity_used - held_capacity

    def __str__(self):
        return f"{self.add_on.title} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"


class HotelBooking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["accommodation", "check_in_date", "check_out_date"])
        ]

    def clean(self):
        if self.check_out_date <= self.check_in_date:
            raise ValidationError("Check-out date must be after check-in date")

        overlapping_bookings = HotelBooking.objects.filter(
            accommodation=self.accommodation,
            check_in_date__lt=self.check_out_date,
            check_out_date__gt=self.check_in_date,
        ).exclude(id=self.id)

        if overlapping_bookings.exists():
            raise ValidationError(
                "This accommodation is already booked for the selected dates"
            )

    def __str__(self):
        return f"Booking for {self.accommodation.title} ({self.check_in_date} to {self.check_out_date})"


class RoomHold(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, null=True, blank=True
    )
    session_id = models.CharField(max_length=36, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["room", "expires_at"]),
            models.Index(fields=["session_id", "expires_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def extend_hold(self, extra_minutes=5):
        self.expires_at += timedelta(minutes=extra_minutes)
        self.save()

    def __str__(self):
        if self.user:
            return f"Hold for {self.quantity} {self.room.title} by {self.user.username}"
        return (
            f"Hold for {self.quantity} {self.room.title} (Session: {self.session_id})"
        )


class TicketHold(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, null=True, blank=True
    )
    session_id = models.CharField(max_length=36, null=True, blank=True)
    pricing_plan = models.ForeignKey(PricingPlan, on_delete=models.CASCADE)
    number_of_tickets = models.PositiveIntegerField()
    room_holds = models.ManyToManyField(RoomHold, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["pricing_plan", "expires_at"]),
            models.Index(fields=["session_id", "expires_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def extend_hold(self, extra_minutes=5):
        self.expires_at += timedelta(minutes=extra_minutes)
        self.save()
        # Also extend all associated room holds
        for room_hold in self.room_holds.all():
            room_hold.extend_hold(extra_minutes)

    def __str__(self):
        user_info = self.user.username if self.user else f"Session {self.session_id}"
        return f"Hold for {self.number_of_tickets} tickets by {user_info}"


class Booking(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("CONFIRMED", "Confirmed"),
        ("CANCELLED", "Cancelled"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    event_date = models.ForeignKey(EventDate, on_delete=models.CASCADE)
    pricing_plan = models.ForeignKey(PricingPlan, on_delete=models.CASCADE)
    group_size = models.ForeignKey(GroupSize, on_delete=models.CASCADE)
    hotel_booking = models.ForeignKey(HotelBooking, on_delete=models.CASCADE, null=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True)
    add_ons = models.ManyToManyField(AddOn, blank=True)
    ticket_hold = models.ForeignKey(
        TicketHold, on_delete=models.SET_NULL, null=True, blank=True
    )
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def validate_tickets(self):
        tickets_needed = self.group_size.number_of_persons

        # Check ticket availability for pricing plan
        if self.pricing_plan.get_available_tickets() < tickets_needed:
            raise ValidationError(
                f"Not enough tickets available for pricing plan {self.pricing_plan.title}"
            )

        # Check ticket availability for accommodation if selected
        if (
            self.hotel_booking
            and self.hotel_booking.accommodation.available_tickets < tickets_needed
        ):
            raise ValidationError(
                f"Not enough tickets available for accommodation {self.hotel_booking.accommodation.title}"
            )

        # Check ticket availability for room if selected
        if self.room and self.room.available_rooms < tickets_needed:
            raise ValidationError(
                f"Not enough rooms available for room {self.room.title}"
            )

        # Check ticket availability for each add-on
        for add_on in self.add_ons.all():
            if add_on.get_available_tickets() < tickets_needed:
                raise ValidationError(
                    f"Not enough tickets available for add-on {add_on.title}"
                )

    def update_tickets(self):
        tickets_needed = self.group_size.number_of_persons

        # Update accommodation and room tickets
        if self.hotel_booking:
            self.hotel_booking.accommodation.available_tickets -= tickets_needed
            self.hotel_booking.accommodation.save()

        if self.room:
            self.room.available_rooms -= tickets_needed
            self.room.save()

        # For add-ons, we don't need to update availability since it's calculated dynamically
        # The get_available_tickets() method will automatically account for this booking
        pass

    def calculate_total_price(self):
        total = (
            self.pricing_plan.price
            + self.group_size.base_price
            + (self.room.price if self.room else 0)
            + (self.hotel_booking.accommodation.price if self.hotel_booking else 0)
        )
        total += sum(add_on.price for add_on in self.add_ons.all())
        return total

    def save(self, *args, **kwargs):
        if self.pk is None:  # Only validate and update tickets on creation
            self.validate_tickets()
            self.total_price = self.calculate_total_price()
            super().save(*args, **kwargs)
            self.update_tickets()
            if self.ticket_hold:
                self.ticket_hold.delete()  # Remove hold once booking is confirmed
        else:
            self.total_price = self.calculate_total_price()
            super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.id} - {self.user.username}"


class BookingAddOn(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="booking_addons"
    )
    add_on = models.ForeignKey(AddOn, on_delete=models.CASCADE)
    time_slot = models.ForeignKey(
        AddOnTimeSlot, on_delete=models.CASCADE, null=True, blank=True
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.time_slot and self.time_slot.add_on != self.add_on:
            raise ValidationError("Time slot must belong to the selected add-on")

    def __str__(self):
        return f"{self.booking.id} - {self.add_on.title}"
