from django.contrib import admin

from .models import DisponibiliteEnseignant, Filiere, VoteEtudiant


@admin.register(Filiere)
class FiliereAdmin(admin.ModelAdmin):
    list_display = ("nom", "statut", "pourcentage_oui", "nb_enseignants_disponibles", "date_creation")
    list_filter = ("statut",)
    search_fields = ("nom",)
    readonly_fields = ("nb_votes_oui", "nb_votes_non", "pourcentage_oui", "nb_enseignants_disponibles")


admin.site.register(VoteEtudiant)
admin.site.register(DisponibiliteEnseignant)
