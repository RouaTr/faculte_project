from django.conf import settings
from django.db import models
from django.db.models import Count, Q
from django.utils import timezone


class Filiere(models.Model):
    EN_VOTE = "en_vote"
    OUVERTE = "ouverte"
    REFUSEE = "refusee"
    STATUT_CHOICES = [
        (EN_VOTE, "En cours de vote"),
        (OUVERTE, "Classe ouverte"),
        (REFUSEE, "Non retenue"),
    ]

    nom = models.CharField("nom de la filière", max_length=120, unique=True)
    description = models.TextField("description", blank=True)

    # Résultats : enregistrés directement dans la filière, recalculés à chaque vote.
    nb_votes_oui = models.PositiveIntegerField("votes oui", default=0, editable=False)
    nb_votes_non = models.PositiveIntegerField("votes non", default=0, editable=False)
    pourcentage_oui = models.FloatField("pourcentage de oui", default=0, editable=False)
    nb_enseignants_disponibles = models.PositiveIntegerField("enseignants disponibles", default=0, editable=False)

    statut = models.CharField("statut", max_length=10, choices=STATUT_CHOICES, default=EN_VOTE, db_index=True)
    date_creation = models.DateTimeField("créée le", auto_now_add=True)
    date_decision = models.DateTimeField("décision prise le", null=True, blank=True)

    etudiants = models.ManyToManyField("accounts.Etudiant", through="VoteEtudiant", related_name="filieres_votees")
    enseignants = models.ManyToManyField("accounts.Enseignant", through="DisponibiliteEnseignant",
                                         related_name="filieres_proposees")

    class Meta:
        ordering = ["-date_creation"]
        verbose_name = "filière"

    def __str__(self):
        return self.nom

    # --- Règles ---------------------------------------------------------
    @property
    def seuil(self):
        return settings.FILIERE_SEUIL_POURCENTAGE

    @property
    def min_enseignants(self):
        return settings.FILIERE_MIN_ENSEIGNANTS

    @property
    def vote_ouvert(self):
        return self.statut == self.EN_VOTE

    @property
    def nb_votes_total(self):
        return self.nb_votes_oui + self.nb_votes_non

    @property
    def pourcentage_non(self):
        return round(100 - self.pourcentage_oui, 1) if self.nb_votes_total else 0

    @property
    def seuil_atteint(self):
        return self.nb_votes_total > 0 and self.pourcentage_oui >= self.seuil

    @property
    def enseignants_suffisants(self):
        return self.nb_enseignants_disponibles >= self.min_enseignants

    @property
    def recommandation(self):
        """True si les résultats justifient l'ouverture de la classe."""
        return self.seuil_atteint and self.enseignants_suffisants

    @property
    def taux_participation(self):
        from accounts.models import Etudiant

        total = Etudiant.objects.count()
        return round(self.nb_votes_total / total * 100, 1) if total else 0

    # --- Actions --------------------------------------------------------
    def calculer_pourcentage(self):
        oui, non = self.nb_votes_oui, self.nb_votes_non
        total = oui + non
        return round(oui / total * 100, 1) if total else 0.0

    def recalculer(self):
        """Recompte votes et disponibilités, puis enregistre les résultats."""
        votes = self.votes.aggregate(
            oui=Count("pk", filter=Q(choix=True)), non=Count("pk", filter=Q(choix=False)))
        self.nb_votes_oui = votes["oui"]
        self.nb_votes_non = votes["non"]
        self.pourcentage_oui = self.calculer_pourcentage()
        self.nb_enseignants_disponibles = self.disponibilites.filter(peut_enseigner=True).count()
        Filiere.objects.filter(pk=self.pk).update(
            nb_votes_oui=self.nb_votes_oui, nb_votes_non=self.nb_votes_non,
            pourcentage_oui=self.pourcentage_oui,
            nb_enseignants_disponibles=self.nb_enseignants_disponibles)

    def ajouter_vote(self, etudiant, choix):
        vote, _ = VoteEtudiant.objects.update_or_create(
            etudiant=etudiant, filiere=self, defaults={"choix": bool(choix)})
        return vote

    def ajouter_disponibilite(self, enseignant, peut_enseigner, commentaire=""):
        dispo, _ = DisponibiliteEnseignant.objects.update_or_create(
            enseignant=enseignant, filiere=self,
            defaults={"peut_enseigner": bool(peut_enseigner), "commentaire": commentaire})
        return dispo

    def decider(self, ouvrir=None):
        """Clôt le vote. Sans argument, suit la recommandation de la plateforme."""
        self.recalculer()
        if ouvrir is None:
            ouvrir = self.recommandation
        self.statut = self.OUVERTE if ouvrir else self.REFUSEE
        self.date_decision = timezone.now()
        self.save(update_fields=["statut", "date_decision"])

    def rouvrir(self):
        self.statut = self.EN_VOTE
        self.date_decision = None
        self.save(update_fields=["statut", "date_decision"])


class VoteEtudiant(models.Model):
    etudiant = models.ForeignKey("accounts.Etudiant", on_delete=models.CASCADE, related_name="votes")
    filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name="votes")
    choix = models.BooleanField("veut cette filière", help_text="Vrai = oui, faux = non")
    date_vote = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["etudiant", "filiere"], name="un_vote_par_etudiant_et_filiere")]
        verbose_name = "vote d'étudiant"
        verbose_name_plural = "votes d'étudiants"

    def __str__(self):
        return f"{self.etudiant} → {self.filiere} : {'oui' if self.choix else 'non'}"


class DisponibiliteEnseignant(models.Model):
    enseignant = models.ForeignKey("accounts.Enseignant", on_delete=models.CASCADE, related_name="disponibilites")
    filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name="disponibilites")
    peut_enseigner = models.BooleanField("peut enseigner la filière")
    commentaire = models.CharField("commentaire", max_length=200, blank=True)
    date_reponse = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["enseignant", "filiere"], name="une_reponse_par_enseignant_et_filiere")]
        verbose_name = "disponibilité d'enseignant"
        verbose_name_plural = "disponibilités d'enseignants"

    def __str__(self):
        return f"{self.enseignant} → {self.filiere} : {'peut' if self.peut_enseigner else 'ne peut pas'}"
