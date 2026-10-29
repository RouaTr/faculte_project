from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Enseignant, Etudiant, Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ("username", "last_name", "first_name", "email", "role", "is_active")
    list_filter = ("role", "is_active")
    fieldsets = UserAdmin.fieldsets + (("Rôle", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Rôle", {"fields": ("role",)}),)


admin.site.register(Etudiant)
admin.site.register(Enseignant)
