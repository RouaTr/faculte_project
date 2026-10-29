from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("filieres/", views.FiliereListView.as_view(), name="filiere_list"),
    path("filieres/nouvelle/", views.FiliereCreateView.as_view(), name="filiere_create"),
    path("filieres/<int:pk>/", views.FiliereDetailView.as_view(), name="filiere_detail"),
    path("filieres/<int:pk>/modifier/", views.FiliereUpdateView.as_view(), name="filiere_update"),
    path("filieres/<int:pk>/supprimer/", views.FiliereDeleteView.as_view(), name="filiere_delete"),
    path("filieres/<int:pk>/voter/", views.voter, name="filiere_voter"),
    path("filieres/<int:pk>/disponibilite/", views.disponibilite, name="filiere_disponibilite"),
    path("filieres/<int:pk>/decider/", views.decider, name="filiere_decider"),
    path("filieres/<int:pk>/rouvrir/", views.rouvrir, name="filiere_rouvrir"),
]
