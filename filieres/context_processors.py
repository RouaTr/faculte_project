from django.conf import settings


def regles(request):
    user = getattr(request, "user", None)
    return {
        "peut_decider": bool(user and user.is_authenticated and user.role in settings.FILIERE_DECISION_ROLES),
    }
