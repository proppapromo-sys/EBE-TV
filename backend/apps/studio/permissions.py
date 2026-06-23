from rest_framework.permissions import BasePermission


class IsCreator(BasePermission):
    """Authenticated users who have enabled creator mode (or staff)."""
    message = "Enable creator mode first (POST /api/studio/enable)."

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (u.is_creator or u.is_staff))
