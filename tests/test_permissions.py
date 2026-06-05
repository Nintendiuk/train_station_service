"""
Tests for authentication and permission enforcement.

Verify 401 (unauthenticated) and 403 (authenticated but unauthorised)
responses, and that admins can perform write operations.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def jwt_client(user) -> APIClient:
    """Return an APIClient authenticated with a JWT for *user*."""
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
    )
    return client


# ---------------------------------------------------------------------------
# Unauthenticated access
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUnauthenticatedAccess:
    """Anonymous requests should receive 401 on all protected endpoints."""

    def test_stations_list_requires_auth(self):
        """GET /api/stations/ without token → 401."""
        client = APIClient()
        url = reverse("train_station:station-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_trains_list_requires_auth(self):
        """GET /api/trains/ without token → 401."""
        client = APIClient()
        url = reverse("train_station:train-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_orders_list_requires_auth(self):
        """GET /api/orders/ without token → 401."""
        client = APIClient()
        url = reverse("train_station:order-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_journeys_list_requires_auth(self):
        """GET /api/journeys/ without token → 401."""
        client = APIClient()
        url = reverse("train_station:journey-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Regular user – read vs write
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRegularUserPermissions:
    """Authenticated non-staff users can read but not write admin resources."""

    def test_regular_user_can_list_stations(self, regular_user):
        """Authenticated regular user can GET stations."""
        client = jwt_client(regular_user)
        url = reverse("train_station:station-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_regular_user_cannot_create_station(self, regular_user):
        """Non-staff user POST to stations → 403."""
        client = jwt_client(regular_user)
        url = reverse("train_station:station-list")
        response = client.post(
            url,
            {"name": "Odesa", "latitude": 46.48, "longitude": 30.72},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_regular_user_cannot_create_train_type(self, regular_user):
        """Non-staff user POST to train-types → 403."""
        client = jwt_client(regular_user)
        url = reverse("train_station:traintype-list")
        response = client.post(
            url, {"name": "Freight"}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_regular_user_cannot_delete_station(
        self, regular_user, station_kyiv
    ):
        """Non-staff user DELETE on a station → 403."""
        client = jwt_client(regular_user)
        url = reverse(
            "train_station:station-detail",
            kwargs={"pk": station_kyiv.pk},
        )
        response = client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_regular_user_can_list_journeys(self, regular_user):
        """Authenticated regular user can GET journeys."""
        client = jwt_client(regular_user)
        url = reverse("train_station:journey-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK


# ---------------------------------------------------------------------------
# Admin user – full access
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAdminUserPermissions:
    """Admin/staff users should have full write access."""

    def test_admin_can_create_station(self, admin_user):
        """Staff user POST to stations → 201."""
        client = jwt_client(admin_user)
        url = reverse("train_station:station-list")
        response = client.post(
            url,
            {"name": "Odesa", "latitude": 46.48, "longitude": 30.72},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_admin_can_create_train_type(self, admin_user):
        """Staff user POST to train-types → 201."""
        client = jwt_client(admin_user)
        url = reverse("train_station:traintype-list")
        response = client.post(
            url, {"name": "Freight"}, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_admin_can_delete_station(self, admin_user, station_kyiv):
        """Staff user DELETE on a station → 204."""
        client = jwt_client(admin_user)
        url = reverse(
            "train_station:station-detail",
            kwargs={"pk": station_kyiv.pk},
        )
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT


# ---------------------------------------------------------------------------
# Order ownership
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestOrderOwnership:
    """Users should only see their own orders."""

    def test_user_sees_own_orders(self, regular_user, order):
        """Regular user GET /orders/ returns only their orders."""
        client = jwt_client(regular_user)
        url = reverse("train_station:order-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        items = data["results"] if isinstance(data, dict) else data
        ids = [o["id"] for o in items]
        assert order.pk in ids

    def test_other_user_cannot_see_orders(self, db, order):
        """Another user should not see someone else's order."""
        from train_station.models import User

        other = User.objects.create_user(
            email="other@example.com", password="otherpass"
        )
        client = jwt_client(other)
        url = reverse("train_station:order-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        items = data["results"] if isinstance(data, dict) else data
        ids = [o["id"] for o in items]
        assert order.pk not in ids


# ---------------------------------------------------------------------------
# JWT token endpoints
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestJWTEndpoints:
    """Test the token obtain and refresh endpoints."""

    def test_obtain_token(self, regular_user):
        """POST /api/token/ with valid credentials → 200 with tokens."""
        client = APIClient()
        url = reverse("train_station:token_obtain_pair")
        response = client.post(
            url,
            {"email": "user@example.com", "password": "userpass"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_obtain_token_invalid_credentials(self, regular_user):
        """POST /api/token/ with wrong password → 401."""
        client = APIClient()
        url = reverse("train_station:token_obtain_pair")
        response = client.post(
            url,
            {"email": "user@example.com", "password": "wrong"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token(self, regular_user):
        """POST /api/token/refresh/ with valid refresh → 200."""
        client = APIClient()
        refresh = RefreshToken.for_user(regular_user)
        url = reverse("train_station:token_refresh")
        response = client.post(
            url, {"refresh": str(refresh)}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
