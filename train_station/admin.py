from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Station, TrainType, Train, Route,
    Crew, Journey, Order, Ticket
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'is_staff')


admin.site.register(Station)
admin.site.register(TrainType)
admin.site.register(Crew)


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [TicketInline]
    list_display = ["id", "user", "created_at"]


@admin.register(Train)
class TrainAdmin(admin.ModelAdmin):
    list_display = ["name", "cargo_num", "places_in_cargo",
                    "train_type", "capacity"]


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ["source", "destination", "distance"]
    list_filter = ["source", "destination"]


@admin.register(Journey)
class JourneyAdmin(admin.ModelAdmin):
    list_display = ["route", "train", "departure_time", "arrival_time"]
    list_filter = ["departure_time", "route"]
