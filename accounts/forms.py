from django import forms
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from .models import Enseignant, Etudiant, Utilisateur

VIDE = [("", "— Choisir —")]


class UtilisateurForm(forms.ModelForm):
    """Création et modification d'un utilisateur, avec son profil selon le rôle."""

    password1 = forms.CharField(label="Mot de passe", required=False, strip=False,
                                widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    password2 = forms.CharField(label="Confirmer le mot de passe", required=False, strip=False,
                                widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    matricule = forms.CharField(label="Matricule", max_length=30, required=False)
    niveau = forms.ChoiceField(label="Niveau", choices=VIDE + Etudiant.NIVEAUX, required=False)
    specialite = forms.CharField(label="Spécialité", max_length=100, required=False)
    grade = forms.ChoiceField(label="Grade", choices=VIDE + Enseignant.GRADES, required=False)

    class Meta:
        model = Utilisateur
        fields = ["first_name", "last_name", "email", "username", "role", "is_active"]
        labels = {"first_name": "Prénom", "last_name": "Nom", "email": "Adresse e-mail",
                  "username": "Identifiant de connexion", "role": "Rôle", "is_active": "Compte actif"}
        help_texts = {"username": "Lettres, chiffres et @/./+/-/_ uniquement."}

    def __init__(self, *args, acteur=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.acteur = acteur
        self.est_modification = bool(self.instance.pk)
        for nom in ("first_name", "last_name", "email"):
            self.fields[nom].required = True

        if self.est_modification:
            self.fields["role"].disabled = True
            self.fields["role"].help_text = "Le rôle ne peut pas être modifié après la création."
            self.fields["password1"].help_text = "Laissez vide pour conserver le mot de passe actuel."
            self._charger_profil()
        else:
            del self.fields["is_active"]
            self.fields["password1"].required = True
            self.fields["password2"].required = True

    def _charger_profil(self):
        user = self.instance
        if hasattr(user, "etudiant"):
            self.fields["matricule"].initial = user.etudiant.matricule
            self.fields["niveau"].initial = user.etudiant.niveau
        if hasattr(user, "enseignant"):
            self.fields["specialite"].initial = user.enseignant.specialite
            self.fields["grade"].initial = user.enseignant.grade

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        doublon = Utilisateur.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if doublon.exists():
            raise forms.ValidationError("Un compte utilise déjà cette adresse e-mail.")
        return email

    def clean_is_active(self):
        actif = self.cleaned_data.get("is_active")
        if not actif and self.acteur and self.instance.pk == self.acteur.pk:
            raise forms.ValidationError("Vous ne pouvez pas désactiver votre propre compte.")
        return actif

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError("Les deux mots de passe ne correspondent pas.")
            validate_password(p1, self.instance)
        return p2

    def clean(self):
        data = super().clean()
        role = data.get("role") or self.instance.role
        if role == Utilisateur.ETUDIANT:
            for champ in ("matricule", "niveau"):
                if not data.get(champ):
                    self.add_error(champ, "Ce champ est obligatoire pour un étudiant.")
            matricule = data.get("matricule")
            if matricule:
                doublon = Etudiant.objects.filter(matricule__iexact=matricule)
                if self.est_modification and hasattr(self.instance, "etudiant"):
                    doublon = doublon.exclude(pk=self.instance.etudiant.pk)
                if doublon.exists():
                    self.add_error("matricule", "Ce matricule est déjà attribué.")
        elif role == Utilisateur.ENSEIGNANT:
            for champ in ("specialite", "grade"):
                if not data.get(champ):
                    self.add_error(champ, "Ce champ est obligatoire pour un enseignant.")
        return data

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("password1"):
            user.set_password(self.cleaned_data["password1"])
        user.save()
        data = self.cleaned_data
        if user.role == Utilisateur.ETUDIANT:
            Etudiant.objects.update_or_create(
                utilisateur=user, defaults={"matricule": data["matricule"], "niveau": data["niveau"]})
        elif user.role == Utilisateur.ENSEIGNANT:
            Enseignant.objects.update_or_create(
                utilisateur=user, defaults={"specialite": data["specialite"], "grade": data["grade"]})
        return user
