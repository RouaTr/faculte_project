from django.contrib.auth.models import AbstractUser
from django.db import models


class Utilisateur(AbstractUser):
    """Compte unique de la plateforme. Le rôle est un simple attribut."""

    ADMIN = "admin"
    ENSEIGNANT = "enseignant"
    ETUDIANT = "etudiant"
    ROLE_CHOICES = [
        (ADMIN, "Administrateur"),
        (ENSEIGNANT, "Enseignant"),
        (ETUDIANT, "Étudiant"),
    ]

    # nom = last_name, prenom = first_name (champs hérités d'AbstractUser)
    role = models.CharField("rôle", max_length=20, choices=ROLE_CHOICES, default=ETUDIANT, db_index=True)

    class Meta:
        ordering = ["last_name", "first_name", "username"]
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.ADMIN
        self.is_staff = self.role == self.ADMIN or self.is_superuser
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom_complet

    @property
    def nom_complet(self):
        return self.get_full_name() or self.username

    @property
    def initiales(self):
        lettres = f"{self.first_name[:1]}{self.last_name[:1]}".upper()
        return lettres or self.username[:2].upper()

    @property
    def est_admin(self):
        return self.role == self.ADMIN

    @property
    def est_enseignant(self):
        return self.role == self.ENSEIGNANT

    @property
    def est_etudiant(self):
        return self.role == self.ETUDIANT


class Etudiant(models.Model):
    """Profil étudiant : étend Utilisateur (relation « hérite »)."""

    NIVEAUX = [("1", "1ère année"), ("2", "2ème année"), ("3", "3ème année"), ("4", "4ème année"), ("5", "5ème année")]

    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name="etudiant")
    matricule = models.CharField("matricule", max_length=30, unique=True)
    niveau = models.CharField("niveau", max_length=1, choices=NIVEAUX)

    class Meta:
        ordering = ["utilisateur__last_name", "utilisateur__first_name"]

    def __str__(self):
        return f"{self.utilisateur.nom_complet} ({self.matricule})"

    def voter(self, filiere, choix):
        """Enregistre (ou modifie) le vote de l'étudiant pour une filière."""
        return filiere.ajouter_vote(self, choix)


class Enseignant(models.Model):
    """Profil enseignant : étend Utilisateur (relation « hérite »)."""

    GRADES = [
        ("assistant", "Assistant"),
        ("maitre_assistant", "Maître assistant"),
        ("maitre_conferences", "Maître de conférences"),
        ("professeur", "Professeur"),
        ("vacataire", "Vacataire"),
    ]

    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name="enseignant")
    specialite = models.CharField("spécialité", max_length=100)
    grade = models.CharField("grade", max_length=30, choices=GRADES)

    class Meta:
        ordering = ["utilisateur__last_name", "utilisateur__first_name"]

    def __str__(self):
        return self.utilisateur.nom_complet

    def declarer_disponibilite(self, filiere, peut_enseigner, commentaire=""):
        """Indique si l'enseignant peut enseigner la filière."""
        return filiere.ajouter_disponibilite(self, peut_enseigner, commentaire)
