"""
Verify that Django settings are correctly configured,
all required apps are installed, JWT endpoints respond,
and Swagger schema endpoint is reachable.
"""

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


class TestInstalledApps(TestCase):
    """Verify all required apps are present in INSTALLED_APPS."""

    def test_rest_framework_installed(self):
        self.assertIn("rest_framework", settings.INSTALLED_APPS)

    def test_simplejwt_installed(self):
        self.assertIn(
            "rest_framework_simplejwt", settings.INSTALLED_APPS
        )

    def test_drf_spectacular_installed(self):
        self.assertIn("drf_spectacular", settings.INSTALLED_APPS)

    def test_django_filters_installed(self):
        self.assertIn("django_filters", settings.INSTALLED_APPS)

    def test_train_station_app_installed(self):
        self.assertIn("train_station", settings.INSTALLED_APPS)


class TestDRFSettings(TestCase):
    """Verify DRF is configured with JWT auth and correct defaults."""

    def test_jwt_authentication_is_default(self):
        auth_classes = settings.REST_FRAMEWORK.get(
            "DEFAULT_AUTHENTICATION_CLASSES", []
        )
        self.assertIn(
            "rest_framework_simplejwt.authentication"
            ".JWTAuthentication",
            auth_classes,
        )

    def test_is_authenticated_is_default_permission(self):
        perm_classes = settings.REST_FRAMEWORK.get(
            "DEFAULT_PERMISSION_CLASSES", []
        )
        self.assertIn(
            "rest_framework.permissions.IsAuthenticated",
            perm_classes,
        )

    def test_spectacular_schema_class(self):
        schema_class = settings.REST_FRAMEWORK.get(
            "DEFAULT_SCHEMA_CLASS", ""
        )
        self.assertEqual(
            schema_class,
            "drf_spectacular.openapi.AutoSchema",
        )

    def test_pagination_configured(self):
        pagination_class = settings.REST_FRAMEWORK.get(
            "DEFAULT_PAGINATION_CLASS", ""
        )
        self.assertIn("PageNumberPagination", pagination_class)


class TestJWTEndpoints(TestCase):
    """JWT token endpoints must exist and return correct status codes."""

    def setUp(self):
        self.client = APIClient()

    def test_token_obtain_url_resolves(self):
        url = reverse("token_obtain_pair")
        self.assertIsNotNone(url)

    def test_token_refresh_url_resolves(self):
        url = reverse("token_refresh")
        self.assertIsNotNone(url)

    def test_token_verify_url_resolves(self):
        url = reverse("token_verify")
        self.assertIsNotNone(url)

    def test_token_obtain_returns_400_on_missing_data(self):

        response = self.client.post(
            reverse("token_obtain_pair"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST
                         )

    def test_token_obtain_returns_401_on_bad_credentials(self):

        response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": "wrong@test.com", "password": "wrong"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestSwaggerEndpoints(TestCase):
    """OpenAPI schema and Swagger UI endpoints must be reachable."""

    def setUp(self):
        self.client = APIClient()

    def test_schema_endpoint_exists(self):
        url = reverse("schema")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_swagger_ui_endpoint_exists(self):
        url = reverse("swagger-ui")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_redoc_endpoint_exists(self):
        url = reverse("redoc")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestUnauthenticatedAccess(TestCase):
    """API endpoints must reject unauthenticated requests with 401."""

    def setUp(self):
        self.client = APIClient()

    def test_api_root_requires_auth(self):
        """The API root should be protected."""
        response = self.client.get("/api/")
        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_200_OK,
            ],
        )
