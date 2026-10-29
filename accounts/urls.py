from django.urls import path

from . import views

urlpatterns = [
    path("", views.UtilisateurListView.as_view(), name="utilisateur_list"),
    path("nouveau/", views.UtilisateurCreateView.as_view(), name="utilisateur_create"),
    path("<int:pk>/", views.UtilisateurDetailView.as_view(), name="utilisateur_detail"),
    path("<int:pk>/modifier/", views.UtilisateurUpdateView.as_view(), name="utilisateur_update"),
    path("<int:pk>/supprimer/", views.UtilisateurDeleteView.as_view(), name="utilisateur_delete"),
]
