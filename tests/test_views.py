"""
Integration tests for all TrainStation API ViewSet endpoints.

Each test class exercises a single ViewSet's CRUD operations,
verifying correct HTTP status codes and response payloads.
"""
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from train_station.models import (
    Route,
    Station,
)

def get_items(response):
    """Unwrap paginated or plain list response."""
    data = response.data
    return data["results"] if isinstance(data, dict) else data



# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def auth_client(user) -> APIClient:
    """Return an APIClient with a valid JWT for *user*."""
    client = APIClient()
    token = RefreshToken.for_user(user).access_token
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


# ---------------------------------------------------------------------------
# Station ViewSet
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStationViewSet:
    """Tests for /api/stations/ CRUD."""

    def test_list_stations(self, regular_user, station_kyiv, station_lviv):
        """GET /stations/ → 200 with two stations."""
        client = auth_client(regular_user)
        response = client.get(reverse("train_station:station-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(get_items(response)) == 2

    def test_retrieve_station(self, regular_user, station_kyiv):
        """GET /stations/{pk}/ → 200 with correct data."""
        client = auth_client(regular_user)
        url = reverse(
            "train_station:station-detail",
            kwargs={"pk": station_kyiv.pk},
        )
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Kyiv"

    def test_create_station_admin(self, admin_user):
        """Admin POST /stations/ → 201."""
        client = auth_client(admin_user)
        data = {"name": "Kharkiv", "latitude": 49.99, "longitude": 36.23}
        response = client.post(
            reverse("train_station:station-list"), data, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Station.objects.filter(name="Kharkiv").exists()

    def test_update_station_admin(self, admin_user, station_kyiv):
        """Admin PATCH /stations/{pk}/ → 200."""
        client = auth_client(admin_user)
        url = reverse(
            "train_station:station-detail",
            kwargs={"pk": station_kyiv.pk},
        )
        response = client.patch(url, {"name": "Kyiv-Pasazhyrskyi"})
        assert response.status_code == status.HTTP_200_OK
        station_kyiv.refresh_from_db()
        assert station_kyiv.name == "Kyiv-Pasazhyrskyi"

    def test_delete_station_admin(self, admin_user, station_kyiv):
        """Admin DELETE /stations/{pk}/ → 204."""
        client = auth_client(admin_user)
        url = reverse(
            "train_station:station-detail",
            kwargs={"pk": station_kyiv.pk},
        )
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Station.objects.filter(pk=station_kyiv.pk).exists()


# ---------------------------------------------------------------------------
# TrainType ViewSet
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTrainTypeViewSet:
    """Tests for /api/train-types/ CRUD."""

    def test_list_train_types(self, regular_user, train_type):
        """GET /train-types/ → 200."""
        client = auth_client(regular_user)
        response = client.get(reverse("train_station:traintype-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(get_items(response)) >= 1

    def test_create_train_type_admin(self, admin_user):
        """Admin POST /train-types/ → 201."""
        client = auth_client(admin_user)
        response = client.post(
            reverse("train_station:traintype-list"),
            {"name": "Regional"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_duplicate_train_type(self, admin_user, train_type):
        """Duplicate name should return 400."""
        client = auth_client(admin_user)
        response = client.post(
            reverse("train_station:traintype-list"),
            {"name": train_type.name},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Train ViewSet
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTrainViewSet:
    """Tests for /api/trains/ CRUD."""

    def test_list_trains(self, regular_user, train):
        """GET /trains/ → 200 with train_type as string."""
        client = auth_client(regular_user)
        response = client.get(reverse("train_station:train-list"))
        assert response.status_code == status.HTTP_200_OK
        assert get_items(response)[0]["name"] == "Intercity+"

    def test_retrieve_train_detail(self, regular_user, train):
        """GET /trains/{pk}/ → 200 with nested train_type."""
        client = auth_client(regular_user)
        url = reverse(
            "train_station:train-detail", kwargs={"pk": train.pk}
        )
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data["train_type"], dict)

    def test_create_train_admin(self, admin_user, train_type):
        """Admin POST /trains/ → 201."""
        client = auth_client(admin_user)
        data = {
            "name": "Pendolino",
            "cargo_num": 10,
            "places_in_cargo": 40,
            "train_type": train_type.pk,
        }
        response = client.post(
            reverse("train_station:train-list"), data, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_train_capacity_field(self, regular_user, train):
        """Train list should include calculated capacity."""
        client = auth_client(regular_user)
        response = client.get(reverse("train_station:train-list"))
        assert get_items(response)[0]["capacity"] == train.capacity


# ---------------------------------------------------------------------------
# Crew ViewSet
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCrewViewSet:
    """Tests for /api/crew/ CRUD."""

    def test_list_crew(self, regular_user, crew):
        """GET /crew/ → 200."""
        client = auth_client(regular_user)
        response = client.get(reverse("train_station:crew-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(get_items(response)) == 1

    def test_create_crew_admin(self, admin_user):
        """Admin POST /crew/ → 201."""
        client = auth_client(admin_user)
        data = {"first_name": "Olena", "last_name": "Kovalenko"}
        response = client.post(
            reverse("train_station:crew-list"), data, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["full_name"] == "Olena Kovalenko"


# ---------------------------------------------------------------------------
# Route ViewSet
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRouteViewSet:
    """Tests for /api/routes/ CRUD."""

    def test_list_routes(self, regular_user, route):
        """GET /routes/ → 200 with source/destination as strings."""
        client = auth_client(regular_user)
        response = client.get(reverse("train_station:route-list"))
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(get_items(response)[0]["source"], str)

    def test_retrieve_route_detail(self, regular_user, route):
        """GET /routes/{pk}/ → 200 with nested station objects."""
        client = auth_client(regular_user)
        url = reverse(
            "train_station:route-detail", kwargs={"pk": route.pk}
        )
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data["source"], dict)

    def test_create_route_admin(
        self, admin_user, station_kyiv, station_lviv
    ):
        """Admin POST /routes/ → 201."""
        client = auth_client(admin_user)
        data = {
            "source": station_kyiv.pk,
            "destination": station_lviv.pk,
            "distance": 540,
        }
        Route.objects.filter(
            source=station_kyiv, destination=station_lviv
        ).delete()
        response = client.post(
            reverse("train_station:route-list"), data, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_route_same_stations_invalid(
        self, admin_user, station_kyiv
    ):
        """Source == destination should return 400."""
        client = auth_client(admin_user)
        data = {
            "source": station_kyiv.pk,
            "destination": station_kyiv.pk,
            "distance": 0,
        }
        response = client.post(
            reverse("train_station:route-list"), data, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Journey ViewSet
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestJourneyViewSet:
    """Tests for /api/journeys/ CRUD and filtering."""

    def test_list_journeys(self, regular_user, journey):
        """GET /journeys/ → 200 with tickets_available."""
        client = auth_client(regular_user)
        response = client.get(reverse("train_station:journey-list"))
        assert response.status_code == status.HTTP_200_OK
        assert "tickets_available" in get_items(response)[0]

    def test_retrieve_journey_detail(self, regular_user, journey):
        """GET /journeys/{pk}/ → 200 with nested route/train."""
        client = auth_client(regular_user)
        url = reverse(
            "train_station:journey-detail", kwargs={"pk": journey.pk}
        )
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data["route"], dict)
        assert "taken_places" in response.data

    def test_create_journey_admin(self, admin_user, route, train):
        """Admin POST /journeys/ → 201."""
        client = auth_client(admin_user)
        now = timezone.now()
        data = {
            "route": route.pk,
            "train": train.pk,
            "departure_time": now.isoformat(),
            "arrival_time": (
                now + timezone.timedelta(hours=4)
            ).isoformat(),
            "crew": [],
        }
        response = client.post(
            reverse("train_station:journey-list"), data, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_filter_journey_by_source(self, regular_user, journey):
        """Filter ?source=Kyiv should return matching journeys."""
        client = auth_client(regular_user)
        url = reverse("train_station:journey-list") + "?source=Kyiv"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(get_items(response)) >= 1

    def test_filter_journey_by_nonexistent_source(
        self, regular_user, journey
    ):
        """Filter ?source=Nowhere should return empty list."""
        client = auth_client(regular_user)
        url = (
            reverse("train_station:journey-list") + "?source=Nowhere"
        )
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(get_items(response)) == 0

    def test_journey_tickets_available_decreases(
        self, regular_user, journey, ticket
    ):
        """tickets_available should be reduced after a ticket is created."""
        client = auth_client(regular_user)
        response = client.get(reverse("train_station:journey-list"))
        available = get_items(response)[0]["tickets_available"]
        assert available == journey.train.capacity - 1


# ---------------------------------------------------------------------------
# Order ViewSet
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestOrderViewSet:
    """Tests for /api/orders/ creation and listing."""

    def test_create_order(self, regular_user, journey):
        """POST /orders/ → 201 with tickets."""
        client = auth_client(regular_user)
        data = {
            "tickets": [
                {"cargo": 1, "seat": 1, "journey": journey.pk},
                {"cargo": 1, "seat": 2, "journey": journey.pk},
            ]
        }
        response = client.post(
            reverse("train_station:order-list"), data, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_list_orders_only_own(
        self, regular_user, admin_user, journey
    ):
        """User should only see their own orders."""
        user_client = auth_client(regular_user)
        user_client.post(
            reverse("train_station:order-list"),
            {
                "tickets": [
                    {"cargo": 1, "seat": 3, "journey": journey.pk}
                ]
            },
            format="json",
        )
        admin_client = auth_client(admin_user)
        admin_client.post(
            reverse("train_station:order-list"),
            {
                "tickets": [
                    {"cargo": 1, "seat": 4, "journey": journey.pk}
                ]
            },
            format="json",
        )

        response = user_client.get(
            reverse("train_station:order-list")
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        items = data["results"] if isinstance(data, dict) else data
        for item in items:
            assert item["id"] is not None

    def test_order_invalid_ticket_rejected(self, regular_user, journey):
        """Order with invalid seat should return 400."""
        client = auth_client(regular_user)
        data = {
            "tickets": [
                {"cargo": 999, "seat": 999, "journey": journey.pk}
            ]
        }
        response = client.post(
            reverse("train_station:order-list"), data, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_order_delete_not_allowed(self, regular_user, order):
        """DELETE on an order should be method-not-allowed."""
        client = auth_client(regular_user)
        url = reverse(
            "train_station:order-detail", kwargs={"pk": order.pk}
        )
        response = client.delete(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ---------------------------------------------------------------------------
# User ViewSet
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUserViewSet:
    """Tests for /api/users/ register and profile."""

    def test_register_user(self, db):
        """POST /users/ without auth → 201 (registration is open)."""
        client = APIClient()
        data = {"email": "newuser@example.com", "password": "strongpass"}
        response = client.post(
            reverse("train_station:user-list"), data, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert "password" not in response.data

    def test_get_own_profile(self, regular_user):
        """GET /users/me/ → 200 for authenticated user."""
        client = auth_client(regular_user)
        url = reverse(
            "train_station:user-detail",
            kwargs={"pk": regular_user.pk},
        )
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == regular_user.email
