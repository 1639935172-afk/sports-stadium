from functools import wraps

from django.core.exceptions import PermissionDenied

from .models import UserRole


def has_role(user, role):
    return user.is_authenticated and user.can_login and user.role == role


def is_ordinary_user(user):
    return has_role(user, UserRole.ORDINARY)


def is_stadium_admin(user):
    return has_role(user, UserRole.STADIUM_ADMIN)


def is_system_admin(user):
    return has_role(user, UserRole.SYSTEM_ADMIN)


def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not has_role(request.user, role):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
