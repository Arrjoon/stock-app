from rest_framework.permissions import BasePermission


class HasRole(BasePermission):
    """Allow the request when the user's role is in view.required_roles."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        required = getattr(view, "required_roles", None)
        if not required:
            return True
        return user.role in set(required)


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == user.Role.ADMIN)


class IsAnalystOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role in {user.Role.ADMIN, user.Role.ANALYST}
        )


class IsViewerOrAbove(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
