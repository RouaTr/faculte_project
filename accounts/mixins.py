from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Réserve une vue aux utilisateurs dont le rôle figure dans `roles`."""

    roles = ()

    def test_func(self):
        return self.request.user.role in self.roles


class AdminRequiredMixin(RoleRequiredMixin):
    roles = ("admin",)


def role_required(*roles):
    """Équivalent fonctionnel de RoleRequiredMixin pour les vues-fonctions."""

    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return wrapper

    return decorator
