"""
URL configuration for the train_station application.

Registers all ViewSets with a DefaultRouter and includes
SimpleJWT token endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from train_station.views import (
    CrewViewSet,
    JourneyViewSet,
    OrderViewSet,
    RouteViewSet,
    StationViewSet,
    TrainTypeViewSet,
    TrainViewSet,
    UserViewSet,
)

app_name = "train_station"

router = DefaultRouter()
router.register("stations", StationViewSet, basename="station")
router.register("train-types", TrainTypeViewSet, basename="traintype")
router.register("trains", TrainViewSet, basename="train")
router.register("crew", CrewViewSet, basename="crew")
router.register("routes", RouteViewSet, basename="route")
router.register("journeys", JourneyViewSet, basename="journey")
router.register("orders", OrderViewSet, basename="order")
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
]
