"""
Shared pytest fixtures for TrainStation Service tests.
"""
import pytest
from django.utils import timezone

from train_station.models import (
    Crew,
    Journey,
    Order,
    Route,
    Station,
    Ticket,
    Train,
    TrainType,
    User,
)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


@pytest.fixture
def admin_user(db):
    """Return a staff/admin user."""
    return User.objects.create_superuser(
        email="admin@example.com", password="adminpass"
    )


@pytest.fixture
def regular_user(db):
    """Return a regular (non-staff) user."""
    return User.objects.create_user(
        email="user@example.com", password="userpass"
    )


# ---------------------------------------------------------------------------
# Core domain objects
# ---------------------------------------------------------------------------


@pytest.fixture
def station_kyiv(db):
    """Return a Station instance for Kyiv."""
    return Station.objects.create(
        name="Kyiv", latitude=50.45, longitude=30.52
    )


@pytest.fixture
def station_lviv(db):
    """Return a Station instance for Lviv."""
    return Station.objects.create(
        name="Lviv", latitude=49.84, longitude=24.03
    )


@pytest.fixture
def train_type(db):
    """Return a TrainType instance."""
    return TrainType.objects.create(name="Express")


@pytest.fixture
def train(db, train_type):
    """Return a Train instance with 5 cargos × 20 seats."""
    return Train.objects.create(
        name="Intercity+",
        cargo_num=5,
        places_in_cargo=20,
        train_type=train_type,
    )


@pytest.fixture
def route(db, station_kyiv, station_lviv):
    """Return a Route from Kyiv to Lviv."""
    return Route.objects.create(
        source=station_kyiv,
        destination=station_lviv,
        distance=540,
    )


@pytest.fixture
def crew(db):
    """Return a Crew instance."""
    return Crew.objects.create(
        first_name="Ivan", last_name="Petrenko"
    )


@pytest.fixture
def journey(db, route, train):
    """Return a Journey on the Kyiv→Lviv route."""
    now = timezone.now()
    return Journey.objects.create(
        route=route,
        train=train,
        departure_time=now,
        arrival_time=now + timezone.timedelta(hours=5),
    )


@pytest.fixture
def order(db, regular_user):
    """Return an Order for the regular user."""
    return Order.objects.create(user=regular_user)


@pytest.fixture
def ticket(db, journey, order):
    """Return a valid Ticket in the journey/order."""
    return Ticket.objects.create(
        cargo=1,
        seat=1,
        journey=journey,
        order=order,
    )
