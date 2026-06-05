"""
Custom DRF permissions for the TrainStation Service.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import APIView


class IsAdminOrReadOnly(BasePermission):
    """
    Allow read access to any authenticated user.
    Write access (POST/PUT/PATCH/DELETE) is restricted to admin/staff only.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Return True for safe methods or staff users."""
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_staff)


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: owner or admin may access the object.
    List-level permission requires authentication only.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Require authentication for all actions."""
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(
        self, request: Request, view: APIView, obj
    ) -> bool:
        """Allow access if requester is the owner or a staff member."""
        if request.user.is_staff:
            return True
        return getattr(obj, "user", None) == request.user
