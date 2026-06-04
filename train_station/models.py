"""
Domain models for the TrainStation Service.

Models
------
User, Station, TrainType, Train, Route,
Crew, Journey, Order, Ticket
"""
import os
import uuid

from django.conf import settings
from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager,
)
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


# ---------------------------------------------------------------------------
# Custom User
# ---------------------------------------------------------------------------


class UserManager(BaseUserManager):
    """Manager that uses email as the unique identifier."""

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields,
    ) -> "User":
        """Create and save a regular user."""
        if not email:
            raise ValueError(_("Email must be set."))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields,
    ) -> "User":
        """Create and save a superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user model with email login."""

    username = None  # type: ignore[assignment]
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()  # type: ignore[assignment]

    def __str__(self) -> str:
        return self.email


# ---------------------------------------------------------------------------
# Station
# ---------------------------------------------------------------------------


class Station(models.Model):
    """A railway station with geographic coordinates."""

    name = models.CharField(max_length=255, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Train infrastructure
# ---------------------------------------------------------------------------


class TrainType(models.Model):
    """Category of train (e.g., Express, Regional)."""

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


def train_image_path(instance: "Train", filename: str) -> str:
    """Build a unique upload path for a train image."""
    _, ext = os.path.splitext(filename)
    return os.path.join("uploads", "trains", f"{uuid.uuid4()}{ext}")


class Train(models.Model):
    """A train with capacity information."""

    name = models.CharField(max_length=255)
    cargo_num = models.PositiveIntegerField()
    places_in_cargo = models.PositiveIntegerField()
    train_type = models.ForeignKey(
        TrainType,
        on_delete=models.CASCADE,
        related_name="trains",
    )
    image = models.ImageField(
        upload_to=train_image_path,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["name"]

    @property
    def capacity(self) -> int:
        """Total seat count across all cargo units."""
        return self.cargo_num * self.places_in_cargo

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Route & Crew
# ---------------------------------------------------------------------------


class Route(models.Model):
    """A directional route between two stations."""

    source = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="departing_routes",
    )
    destination = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="arriving_routes",
    )
    distance = models.PositiveIntegerField(help_text="Distance in km.")

    class Meta:
        unique_together = ("source", "destination")
        ordering = ["source__name", "destination__name"]

    def clean(self) -> None:
        """Ensure source and destination differ."""
        if self.source_id and self.destination_id:
            if self.source_id == self.destination_id:
                raise ValidationError(
                    "Source and destination must be different stations."
                )

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.source} → {self.destination}"


class Crew(models.Model):
    """A crew member (first + last name)."""

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    class Meta:
        ordering = ["last_name", "first_name"]

    @property
    def full_name(self) -> str:
        """Return concatenated full name."""
        return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        return self.full_name


# ---------------------------------------------------------------------------
# Journey
# ---------------------------------------------------------------------------


class Journey(models.Model):
    """A specific train run on a route at a given time."""

    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="journeys",
    )
    train = models.ForeignKey(
        Train,
        on_delete=models.CASCADE,
        related_name="journeys",
    )
    crew = models.ManyToManyField(
        Crew,
        related_name="journeys",
        blank=True,
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    class Meta:
        ordering = ["departure_time"]

    def clean(self) -> None:
        """Ensure arrival is after departure."""
        if self.departure_time and self.arrival_time:
            if self.arrival_time <= self.departure_time:
                raise ValidationError(
                    "Arrival time must be after departure time."
                )

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return (
            f"{self.route} "
            f"[{self.departure_time:%Y-%m-%d %H:%M}]"
        )


# ---------------------------------------------------------------------------
# Order & Ticket
# ---------------------------------------------------------------------------


class Order(models.Model):
    """A customer's purchase session grouping one or more tickets."""

    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order #{self.pk} by {self.user}"


class Ticket(models.Model):
    """A single seat reservation within an Order on a Journey."""

    cargo = models.PositiveIntegerField()
    seat = models.PositiveIntegerField()
    journey = models.ForeignKey(
        Journey,
        on_delete=models.CASCADE,
        related_name="tickets",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets",
    )

    class Meta:
        unique_together = ("journey", "cargo", "seat")
        ordering = ["cargo", "seat"]

    @staticmethod
    def validate_seat(
        cargo: int,
        seat: int,
        train: Train,
        error_to_raise: type[Exception],
    ) -> None:
        """Validate cargo/seat numbers against train capacity."""
        for attr, value, limit in (
            ("cargo", cargo, train.cargo_num),
            ("seat", seat, train.places_in_cargo),
        ):
            if not (1 <= value <= limit):
                raise error_to_raise(
                    {
                        attr: (
                            f"{attr.capitalize()} number must be "
                            f"between 1 and {limit}. Got {value}."
                        )
                    }
                )

    def clean(self) -> None:
        Ticket.validate_seat(
            self.cargo,
            self.seat,
            self.journey.train,
            ValidationError,
        )

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return (
            f"Ticket cargo={self.cargo} seat={self.seat} "
            f"journey={self.journey_id}"
        )
