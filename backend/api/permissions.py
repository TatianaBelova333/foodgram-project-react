from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsObjOwnerOrAdminOrReadOnly(BasePermission):

    message = ("Editing or deleting other users'"
               "recipes is not allowed")

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
            or request.user.is_admin
        )


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
