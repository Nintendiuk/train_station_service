"""
DRF serializers for the TrainStation Service.

Each serializer follows a list / detail / write pattern where needed.
"""
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from train_station.models import (
    Crew,
    Journey,
    Order,
    Route,
    Station,
    Ticket,
    Train,
    TrainType,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------


class UserSerializer(serializers.ModelSerializer):
    """Serialize User for registration/profile."""

    class Meta:
        model = User
        fields = ["id", "email", "password", "is_staff"]
        read_only_fields = ["is_staff"]
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 5}
        }

    def create(self, validated_data: dict) -> User:
        """Create user with hashed password."""
        return User.objects.create_user(**validated_data)

    def update(self, instance: User, validated_data: dict) -> User:
        """Update user; hash password if provided."""
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


# ---------------------------------------------------------------------------
# Station
# ---------------------------------------------------------------------------


class StationSerializer(serializers.ModelSerializer):
    """Serialize Station for list/detail views."""

    class Meta:
        model = Station
        fields = ["id", "name", "latitude", "longitude"]


# ---------------------------------------------------------------------------
# TrainType
# ---------------------------------------------------------------------------


class TrainTypeSerializer(serializers.ModelSerializer):
    """Serialize TrainType."""

    class Meta:
        model = TrainType
        fields = ["id", "name"]


# ---------------------------------------------------------------------------
# Train
# ---------------------------------------------------------------------------


class TrainListSerializer(serializers.ModelSerializer):
    """Flat train list with type name and capacity."""

    train_type = serializers.StringRelatedField()

    class Meta:
        model = Train
        fields = [
            "id",
            "name",
            "cargo_num",
            "places_in_cargo",
            "capacity",
            "train_type",
            "image",
        ]


class TrainDetailSerializer(TrainListSerializer):
    """Detail view: nested TrainType object."""

    train_type = TrainTypeSerializer(read_only=True)


class TrainWriteSerializer(serializers.ModelSerializer):
    """Writable serializer for creating/updating a Train."""

    class Meta:
        model = Train
        fields = [
            "id",
            "name",
            "cargo_num",
            "places_in_cargo",
            "train_type",
        ]


class TrainImageSerializer(serializers.ModelSerializer):
    """Serializer used exclusively for the upload_image action."""

    class Meta:
        model = Train
        fields = ["id", "image"]


# ---------------------------------------------------------------------------
# Crew
# ---------------------------------------------------------------------------


class CrewSerializer(serializers.ModelSerializer):
    """Serialize Crew with full_name property."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Crew
        fields = ["id", "first_name", "last_name", "full_name"]


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


class RouteListSerializer(serializers.ModelSerializer):
    """Flat route list with station names."""

    source = serializers.StringRelatedField()
    destination = serializers.StringRelatedField()

    class Meta:
        model = Route
        fields = ["id", "source", "destination", "distance"]


class RouteDetailSerializer(RouteListSerializer):
    """Detail route with nested Station objects."""

    source = StationSerializer(read_only=True)
    destination = StationSerializer(read_only=True)


class RouteWriteSerializer(serializers.ModelSerializer):
    """Writable serializer for Route."""

    class Meta:
        model = Route
        fields = ["id", "source", "destination", "distance"]

    def validate(self, attrs: dict) -> dict:
        """Ensure source and destination differ."""
        if attrs.get("source") == attrs.get("destination"):
            raise serializers.ValidationError(
                "Source and destination must be different stations."
            )
        return attrs


# ---------------------------------------------------------------------------
# Journey
# ---------------------------------------------------------------------------


class JourneyListSerializer(serializers.ModelSerializer):
    """Flat journey list with tickets_available computed field."""

    route = serializers.StringRelatedField()
    train = serializers.StringRelatedField()
    tickets_available = serializers.SerializerMethodField()

    class Meta:
        model = Journey
        fields = [
            "id",
            "route",
            "train",
            "departure_time",
            "arrival_time",
            "tickets_available",
        ]

    def get_tickets_available(self, obj: Journey) -> int:
        """Compute remaining seats for this journey."""
        taken = obj.tickets.count()
        return obj.train.capacity - taken


class JourneyDetailSerializer(serializers.ModelSerializer):
    """Detail journey with nested objects and seat availability."""

    route = RouteDetailSerializer(read_only=True)
    train = TrainDetailSerializer(read_only=True)
    crew = CrewSerializer(many=True, read_only=True)
    taken_places = serializers.SerializerMethodField()

    class Meta:
        model = Journey
        fields = [
            "id",
            "route",
            "train",
            "crew",
            "departure_time",
            "arrival_time",
            "taken_places",
        ]

    def get_taken_places(self, obj: Journey) -> list[dict]:
        """Return list of {cargo, seat} dicts for booked seats."""
        return list(
            obj.tickets.values("cargo", "seat")
        )


class JourneyWriteSerializer(serializers.ModelSerializer):
    """Writable serializer for creating/updating a Journey."""

    class Meta:
        model = Journey
        fields = [
            "id",
            "route",
            "train",
            "crew",
            "departure_time",
            "arrival_time",
        ]

    def validate(self, attrs: dict) -> dict:
        """Ensure arrival is after departure."""
        dep = attrs.get("departure_time")
        arr = attrs.get("arrival_time")
        if dep and arr and arr <= dep:
            raise serializers.ValidationError(
                "Arrival time must be after departure time."
            )
        return attrs


# ---------------------------------------------------------------------------
# Ticket
# ---------------------------------------------------------------------------


class TicketSerializer(serializers.ModelSerializer):
    """Serialize a single Ticket with validation."""

    def validate(self, attrs: dict) -> dict:
        """Validate cargo/seat against the journey's train."""
        Ticket.validate_seat(
            attrs["cargo"],
            attrs["seat"],
            attrs["journey"].train,
            serializers.ValidationError,
        )
        return attrs

    class Meta:
        model = Ticket
        fields = ["id", "cargo", "seat", "journey"]


class TicketDetailSerializer(TicketSerializer):
    """Detail ticket with nested journey."""

    journey = JourneyListSerializer(read_only=True)


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------


class OrderListSerializer(serializers.ModelSerializer):
    """Order list serializer with ticket count."""

    ticket_count = serializers.IntegerField(
        source="tickets.count", read_only=True
    )

    class Meta:
        model = Order
        fields = ["id", "created_at", "ticket_count"]


class OrderDetailSerializer(serializers.ModelSerializer):
    """Order detail with nested tickets."""

    tickets = TicketDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "created_at", "tickets"]


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an Order with its Tickets atomically."""

    tickets = TicketSerializer(many=True, allow_empty=False)

    class Meta:
        model = Order
        fields = ["id", "tickets", "created_at"]
        read_only_fields = ["created_at"]

    @transaction.atomic
    def create(self, validated_data: dict) -> Order:
        """Create Order + Tickets in a single transaction."""
        tickets_data = validated_data.pop("tickets")
        order = Order.objects.create(**validated_data)
        for ticket_data in tickets_data:
            Ticket.objects.create(order=order, **ticket_data)
        return order
