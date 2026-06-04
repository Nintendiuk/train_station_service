"""
DRF ViewSets for the TrainStation Service.

Each ViewSet selects the appropriate serializer for list/detail/write
actions and applies IsAdminOrReadOnly (or IsOwnerOrAdmin for orders).
"""
from django.db.models import Count, QuerySet
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from train_station.models import (
    Crew,
    Journey,
    Order,
    Route,
    Station,
    Train,
    TrainType,
)
from train_station.permissions import IsAdminOrReadOnly, IsOwnerOrAdmin
from train_station.serializers import (
    CrewSerializer,
    JourneyDetailSerializer,
    JourneyListSerializer,
    JourneyWriteSerializer,
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    RouteDetailSerializer,
    RouteListSerializer,
    RouteWriteSerializer,
    StationSerializer,
    TrainDetailSerializer,
    TrainImageSerializer,
    TrainListSerializer,
    TrainTypeSerializer,
    TrainWriteSerializer,
    UserSerializer,
)
from train_station.models import User


# ---------------------------------------------------------------------------
# User (register / profile)
# ---------------------------------------------------------------------------


@extend_schema_view(
    create=extend_schema(summary="Register a new user"),
    retrieve=extend_schema(summary="Get current user profile"),
    update=extend_schema(summary="Update current user profile"),
)
class UserViewSet(ModelViewSet):
    """ViewSet for user registration and profile management."""

    serializer_class = UserSerializer
    http_method_names = ["get", "post", "put", "patch"]

    def get_permissions(self):
        if self.action == "create":
            return []
        return super().get_permissions()

    def get_queryset(self) -> QuerySet:
        """Return only the current user's record."""
        return User.objects.filter(pk=self.request.user.pk)

    def get_object(self) -> User:
        """Always return the requesting user."""
        return self.request.user


# ---------------------------------------------------------------------------
# Station
# ---------------------------------------------------------------------------


@extend_schema_view(
    list=extend_schema(summary="List all stations"),
    create=extend_schema(summary="Create a station (admin only)"),
    retrieve=extend_schema(summary="Retrieve a station"),
    update=extend_schema(summary="Update a station (admin only)"),
    destroy=extend_schema(summary="Delete a station (admin only)"),
)
class StationViewSet(ModelViewSet):
    """CRUD ViewSet for Station."""

    queryset = Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = [IsAdminOrReadOnly]


# ---------------------------------------------------------------------------
# TrainType
# ---------------------------------------------------------------------------


class TrainTypeViewSet(ModelViewSet):
    """CRUD ViewSet for TrainType."""

    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer
    permission_classes = [IsAdminOrReadOnly]


# ---------------------------------------------------------------------------
# Train
# ---------------------------------------------------------------------------


@extend_schema_view(
    upload_image=extend_schema(
        summary="Upload an image for a train",
        request=TrainImageSerializer,
    )
)
class TrainViewSet(ModelViewSet):
    """CRUD ViewSet for Train with image upload support."""

    queryset = Train.objects.select_related("train_type")
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return TrainListSerializer
        if self.action in ("create", "update", "partial_update"):
            return TrainWriteSerializer
        if self.action == "upload_image":
            return TrainImageSerializer
        return TrainDetailSerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_image(self, request: Request, pk=None) -> Response:
        """Upload or replace the image for a specific train."""
        train = self.get_object()
        serializer = self.get_serializer(
            train, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Crew
# ---------------------------------------------------------------------------


class CrewViewSet(ModelViewSet):
    """CRUD ViewSet for Crew."""

    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    permission_classes = [IsAdminOrReadOnly]


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


class RouteViewSet(ModelViewSet):
    """CRUD ViewSet for Route."""

    queryset = Route.objects.select_related("source", "destination")
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        if self.action in ("create", "update", "partial_update"):
            return RouteWriteSerializer
        return RouteDetailSerializer


# ---------------------------------------------------------------------------
# Journey
# ---------------------------------------------------------------------------


class JourneyViewSet(ModelViewSet):
    """CRUD ViewSet for Journey with seat availability annotation."""

    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self) -> QuerySet:
        """Annotate with tickets_sold for efficient availability calc."""
        qs = (
            Journey.objects
            .select_related(
                "route__source",
                "route__destination",
                "train__train_type",
            )
            .prefetch_related("crew")
            .annotate(tickets_sold=Count("tickets"))
            .order_by("departure_time")
        )

        source = self.request.query_params.get("source")
        destination = self.request.query_params.get("destination")
        date = self.request.query_params.get("date")

        if source:
            qs = qs.filter(route__source__name__icontains=source)
        if destination:
            qs = qs.filter(
                route__destination__name__icontains=destination
            )
        if date:
            qs = qs.filter(departure_time__date=date)

        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return JourneyListSerializer
        if self.action in ("create", "update", "partial_update"):
            return JourneyWriteSerializer
        return JourneyDetailSerializer


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------


class OrderViewSet(ModelViewSet):
    """ViewSet for Orders; scoped to the requesting user."""

    permission_classes = [IsOwnerOrAdmin]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self) -> QuerySet:
        """Return only the current user's orders (admin sees all)."""
        qs = Order.objects.prefetch_related(
            "tickets__journey__route__source",
            "tickets__journey__route__destination",
            "tickets__journey__train",
        )
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "create":
            return OrderCreateSerializer
        return OrderDetailSerializer

    def perform_create(self, serializer) -> None:
        """Attach the requesting user to the new order."""
        serializer.save(user=self.request.user)
