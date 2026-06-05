"""
Tests for TrainStation serializers.

Cover field presence, validation logic, and nested creation.
"""
import pytest
from django.utils import timezone

from train_station.serializers import (
    JourneyWriteSerializer,
    OrderCreateSerializer,
    RouteWriteSerializer,
    TicketSerializer,
    TrainWriteSerializer,
    UserSerializer,
)


# ---------------------------------------------------------------------------
# UserSerializer
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUserSerializer:
    """Tests for UserSerializer."""

    def test_valid_user_creation(self):
        """Valid data should create a user with hashed password."""
        data = {"email": "new@example.com", "password": "securepass"}
        s = UserSerializer(data=data)
        assert s.is_valid(), s.errors
        user = s.save()
        assert user.check_password("securepass")

    def test_password_too_short(self):
        """Password shorter than 5 chars should fail validation."""
        data = {"email": "x@example.com", "password": "abc"}
        s = UserSerializer(data=data)
        assert not s.is_valid()
        assert "password" in s.errors

    def test_password_write_only(self):
        """Password should not appear in serialized output."""
        data = {"email": "y@example.com", "password": "securepass"}
        s = UserSerializer(data=data)
        s.is_valid()
        user = s.save()
        out = UserSerializer(user)
        assert "password" not in out.data

    def test_update_password(self, regular_user):
        """Updating with new password should hash and save it."""
        s = UserSerializer(
            regular_user,
            data={"email": regular_user.email, "password": "newpassword"},
            partial=True,
        )
        assert s.is_valid(), s.errors
        user = s.save()
        assert user.check_password("newpassword")


# ---------------------------------------------------------------------------
# RouteWriteSerializer
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRouteWriteSerializer:
    """Tests for RouteWriteSerializer validation."""

    def test_same_source_destination_invalid(
        self, station_kyiv
    ):
        """Route where source == destination should be invalid."""
        data = {
            "source": station_kyiv.pk,
            "destination": station_kyiv.pk,
            "distance": 0,
        }
        s = RouteWriteSerializer(data=data)
        assert not s.is_valid()
        assert "non_field_errors" in s.errors

    def test_valid_route(self, station_kyiv, station_lviv):
        """A route with different source and destination is valid."""
        data = {
            "source": station_kyiv.pk,
            "destination": station_lviv.pk,
            "distance": 540,
        }
        s = RouteWriteSerializer(data=data)
        assert s.is_valid(), s.errors


# ---------------------------------------------------------------------------
# TrainWriteSerializer
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTrainWriteSerializer:
    """Tests for TrainWriteSerializer."""

    def test_valid_train(self, train_type):
        """Valid data should pass serializer validation."""
        data = {
            "name": "Sapsan",
            "cargo_num": 8,
            "places_in_cargo": 50,
            "train_type": train_type.pk,
        }
        s = TrainWriteSerializer(data=data)
        assert s.is_valid(), s.errors

    def test_missing_name_invalid(self, train_type):
        """Missing name field should produce a validation error."""
        data = {
            "cargo_num": 8,
            "places_in_cargo": 50,
            "train_type": train_type.pk,
        }
        s = TrainWriteSerializer(data=data)
        assert not s.is_valid()
        assert "name" in s.errors


# ---------------------------------------------------------------------------
# JourneyWriteSerializer
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestJourneyWriteSerializer:
    """Tests for JourneyWriteSerializer validation."""

    def test_arrival_before_departure_invalid(
        self, route, train
    ):
        """Arrival ≤ departure should fail validation."""
        now = timezone.now()
        data = {
            "route": route.pk,
            "train": train.pk,
            "departure_time": now.isoformat(),
            "arrival_time": now.isoformat(),
            "crew": [],
        }
        s = JourneyWriteSerializer(data=data)
        assert not s.is_valid()
        assert "non_field_errors" in s.errors

    def test_valid_journey(self, route, train):
        """Journey with arrival after departure is valid."""
        now = timezone.now()
        data = {
            "route": route.pk,
            "train": train.pk,
            "departure_time": now.isoformat(),
            "arrival_time": (
                now + timezone.timedelta(hours=3)
            ).isoformat(),
            "crew": [],
        }
        s = JourneyWriteSerializer(data=data)
        assert s.is_valid(), s.errors


# ---------------------------------------------------------------------------
# TicketSerializer
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTicketSerializer:
    """Tests for TicketSerializer seat validation."""

    def test_invalid_cargo(self, journey):
        """cargo > train.cargo_num should fail validation."""
        data = {"cargo": 999, "seat": 1, "journey": journey.pk}
        s = TicketSerializer(data=data)
        assert not s.is_valid()

    def test_invalid_seat(self, journey):
        """seat > places_in_cargo should fail validation."""
        data = {"cargo": 1, "seat": 999, "journey": journey.pk}
        s = TicketSerializer(data=data)
        assert not s.is_valid()

    def test_valid_ticket(self, journey):
        """Valid cargo/seat should pass validation."""
        data = {"cargo": 1, "seat": 1, "journey": journey.pk}
        s = TicketSerializer(data=data)
        assert s.is_valid(), s.errors


# ---------------------------------------------------------------------------
# OrderCreateSerializer
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestOrderCreateSerializer:
    """Tests for atomic order creation with tickets."""

    def test_create_order_with_tickets(self, regular_user, journey):
        """Order with valid tickets should be created atomically."""
        data = {
            "tickets": [
                {"cargo": 1, "seat": 1, "journey": journey.pk},
                {"cargo": 1, "seat": 2, "journey": journey.pk},
            ]
        }
        s = OrderCreateSerializer(data=data)
        assert s.is_valid(), s.errors
        order = s.save(user=regular_user)
        assert order.pk is not None
        assert order.tickets.count() == 2

    def test_empty_tickets_invalid(self):
        """Order without tickets should be invalid."""
        s = OrderCreateSerializer(data={"tickets": []})
        assert not s.is_valid()
        assert "tickets" in s.errors
