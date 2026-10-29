from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

handler403 = "filieres.views.erreur_403"

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "connexion/",
        auth_views.LoginView.as_view(redirect_authenticated_user=True),
        name="login",
    ),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "mot-de-passe/",
        auth_views.PasswordChangeView.as_view(
            template_name="registration/password_change.html",
            success_url="/mot-de-passe/fait/",
        ),
        name="password_change",
    ),
    path(
        "mot-de-passe/fait/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="registration/password_change_done.html"
        ),
        name="password_change_done",
    ),
    path("utilisateurs/", include("accounts.urls")),
    path("", include("filieres.urls")),
]
