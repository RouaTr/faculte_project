import random

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Enseignant, Etudiant, Utilisateur
from filieres.models import Filiere

MOT_DE_PASSE = "demo12345"

ETUDIANTS = [
    ("Amira", "Ben Salah"), ("Yassine", "Trabelsi"), ("Salma", "Gharbi"), ("Mehdi", "Jlassi"),
    ("Ines", "Mansouri"), ("Omar", "Chaabane"), ("Rania", "Hamdi"), ("Khalil", "Ayari"),
    ("Nour", "Bouzid"), ("Wassim", "Dridi"), ("Syrine", "Karray"), ("Aymen", "Sassi"),
]
ENSEIGNANTS = [
    ("Leila", "Mrad", "Réseaux et cloud", "maitre_conferences"),
    ("Karim", "Ben Ammar", "Systèmes distribués", "professeur"),
    ("Hela", "Zouari", "Intelligence artificielle", "maitre_assistant"),
    ("Slim", "Bouaziz", "Sécurité informatique", "assistant"),
    ("Mouna", "Khemiri", "Bases de données", "maitre_assistant"),
]
FILIERES = [
    ("Cloud Computing", "Concevoir, déployer et exploiter des infrastructures cloud : conteneurs, orchestration, DevOps et architectures serverless."),
    ("Cybersécurité", "Protéger les systèmes et les données : cryptographie, audit, sécurité des réseaux et réponse aux incidents."),
    ("Intelligence artificielle", "Apprentissage automatique, traitement du langage et vision par ordinateur appliqués à des projets concrets."),
]


class Command(BaseCommand):
    help = "Crée des comptes et des filières de démonstration."

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(7)

        admin, cree = Utilisateur.objects.get_or_create(
            username="admin", defaults={"first_name": "Sonia", "last_name": "Hammami",
                                        "email": "admin@faculte.tn", "role": Utilisateur.ADMIN})
        if cree:
            admin.set_password(MOT_DE_PASSE)
            admin.save()

        etudiants = []
        for i, (prenom, nom) in enumerate(ETUDIANTS, start=1):
            user, cree = Utilisateur.objects.get_or_create(
                username=f"etudiant{i}", defaults={"first_name": prenom, "last_name": nom,
                                                   "email": f"etudiant{i}@faculte.tn", "role": Utilisateur.ETUDIANT})
            if cree:
                user.set_password(MOT_DE_PASSE)
                user.save()
            profil, _ = Etudiant.objects.get_or_create(
                utilisateur=user, defaults={"matricule": f"2026{i:04d}", "niveau": str(rng.randint(2, 4))})
            etudiants.append(profil)

        enseignants = []
        for i, (prenom, nom, specialite, grade) in enumerate(ENSEIGNANTS, start=1):
            user, cree = Utilisateur.objects.get_or_create(
                username=f"enseignant{i}", defaults={"first_name": prenom, "last_name": nom,
                                                     "email": f"enseignant{i}@faculte.tn", "role": Utilisateur.ENSEIGNANT})
            if cree:
                user.set_password(MOT_DE_PASSE)
                user.save()
            profil, _ = Enseignant.objects.get_or_create(
                utilisateur=user, defaults={"specialite": specialite, "grade": grade})
            enseignants.append(profil)

        for nom, description in FILIERES:
            Filiere.objects.get_or_create(nom=nom, defaults={"description": description})

        cloud, cyber, ia = (Filiere.objects.get(nom=n) for n, _ in FILIERES)
        # Cloud : fort soutien, étudiants laissés pour que vous puissiez voter avec etudiant11 / etudiant12
        for e in etudiants[:9]:
            cloud.ajouter_vote(e, rng.random() < 0.8)
        for ens in enseignants[:3]:
            cloud.ajouter_disponibilite(ens, True, "Je peux assurer les modules d'infrastructure.")
        # Cybersécurité : vote partagé
        for e in etudiants[:8]:
            cyber.ajouter_vote(e, rng.random() < 0.5)
        cyber.ajouter_disponibilite(enseignants[3], True)
        # IA : déjà décidée
        for e in etudiants:
            ia.ajouter_vote(e, rng.random() < 0.85)
        for ens in enseignants[:4]:
            ia.ajouter_disponibilite(ens, True)
        if ia.vote_ouvert:
            ia.decider()

        self.stdout.write(self.style.SUCCESS("Données de démonstration prêtes."))
        self.stdout.write(f"  Administrateur : admin / {MOT_DE_PASSE}")
        self.stdout.write(f"  Étudiants      : etudiant1 … etudiant{len(ETUDIANTS)} / {MOT_DE_PASSE}")
        self.stdout.write(f"  Enseignants    : enseignant1 … enseignant{len(ENSEIGNANTS)} / {MOT_DE_PASSE}")
