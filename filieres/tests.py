from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Enseignant, Etudiant, Utilisateur
from filieres.models import Filiere, VoteEtudiant


def creer(username, role, **profil):
    user = Utilisateur.objects.create_user(username=username, password="x-secret-123", role=role,
                                           first_name=username.title(), last_name="Test", email=f"{username}@t.tn")
    if role == Utilisateur.ETUDIANT:
        Etudiant.objects.create(utilisateur=user, matricule=f"M-{username}", niveau="2")
    if role == Utilisateur.ENSEIGNANT:
        Enseignant.objects.create(utilisateur=user, specialite="Cloud", grade="professeur")
    return user


class ResultatsTests(TestCase):
    def setUp(self):
        self.filiere = Filiere.objects.create(nom="Cloud")
        self.etus = [creer(f"e{i}", Utilisateur.ETUDIANT).etudiant for i in range(5)]
        self.ens = [creer(f"p{i}", Utilisateur.ENSEIGNANT).enseignant for i in range(3)]

    def test_pourcentage_et_compteurs(self):
        for etu, choix in zip(self.etus, [True, True, True, False, False]):
            etu.voter(self.filiere, choix)
        self.filiere.refresh_from_db()
        self.assertEqual((self.filiere.nb_votes_oui, self.filiere.nb_votes_non), (3, 2))
        self.assertEqual(self.filiere.pourcentage_oui, 60.0)

    def test_changer_son_vote_ne_double_pas(self):
        self.etus[0].voter(self.filiere, True)
        self.etus[0].voter(self.filiere, False)
        self.filiere.refresh_from_db()
        self.assertEqual(VoteEtudiant.objects.count(), 1)
        self.assertEqual((self.filiere.nb_votes_oui, self.filiere.nb_votes_non), (0, 1))

    def test_suppression_utilisateur_recalcule(self):
        self.etus[0].voter(self.filiere, True)
        self.etus[1].voter(self.filiere, False)
        self.etus[0].utilisateur.delete()
        self.filiere.refresh_from_db()
        self.assertEqual((self.filiere.nb_votes_oui, self.filiere.nb_votes_non), (0, 1))

    @override_settings(FILIERE_SEUIL_POURCENTAGE=60, FILIERE_MIN_ENSEIGNANTS=2)
    def test_recommandation(self):
        for etu in self.etus[:4]:
            etu.voter(self.filiere, True)
        self.etus[4].voter(self.filiere, False)
        self.ens[0].declarer_disponibilite(self.filiere, True)
        self.filiere.refresh_from_db()
        self.assertTrue(self.filiere.seuil_atteint)
        self.assertFalse(self.filiere.recommandation)  # un seul enseignant
        self.ens[1].declarer_disponibilite(self.filiere, True)
        self.ens[2].declarer_disponibilite(self.filiere, False)
        self.filiere.refresh_from_db()
        self.assertEqual(self.filiere.nb_enseignants_disponibles, 2)
        self.assertTrue(self.filiere.recommandation)


class VuesTests(TestCase):
    def setUp(self):
        self.admin = creer("boss", Utilisateur.ADMIN)
        self.etu = creer("etu", Utilisateur.ETUDIANT)
        self.ens = creer("prof", Utilisateur.ENSEIGNANT)
        self.filiere = Filiere.objects.create(nom="Cyber")

    def test_acces_anonyme_redirige(self):
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 302)

    def test_dashboards_par_role(self):
        for user in (self.admin, self.etu, self.ens):
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)
            self.assertEqual(self.client.get(reverse("filiere_list")).status_code, 200)
            self.assertEqual(self.client.get(reverse("filiere_detail", args=[self.filiere.pk])).status_code, 200)

    def test_etudiant_vote(self):
        self.client.force_login(self.etu)
        self.client.post(reverse("filiere_voter", args=[self.filiere.pk]), {"choix": "oui"})
        self.filiere.refresh_from_db()
        self.assertEqual(self.filiere.nb_votes_oui, 1)

    def test_enseignant_ne_peut_pas_voter_comme_etudiant(self):
        self.client.force_login(self.ens)
        r = self.client.post(reverse("filiere_voter", args=[self.filiere.pk]), {"choix": "oui"})
        self.assertEqual(r.status_code, 403)

    def test_enseignant_repond(self):
        self.client.force_login(self.ens)
        self.client.post(reverse("filiere_disponibilite", args=[self.filiere.pk]), {"reponse": "oui", "commentaire": "OK"})
        self.filiere.refresh_from_db()
        self.assertEqual(self.filiere.nb_enseignants_disponibles, 1)

    def test_etudiant_ne_voit_pas_les_resultats_pendant_le_vote(self):
        self.client.force_login(self.etu)
        r = self.client.get(reverse("filiere_detail", args=[self.filiere.pk]))
        self.assertContains(r, "publiés une fois la décision")

    def test_vote_clos_refuse(self):
        self.filiere.decider(ouvrir=False)
        self.client.force_login(self.etu)
        self.client.post(reverse("filiere_voter", args=[self.filiere.pk]), {"choix": "oui"})
        self.assertEqual(VoteEtudiant.objects.count(), 0)

    def test_seul_admin_decide_par_defaut(self):
        url = reverse("filiere_decider", args=[self.filiere.pk])
        self.client.force_login(self.ens)
        self.assertEqual(self.client.post(url, {"decision": "ouvrir"}).status_code, 403)
        self.client.force_login(self.admin)
        self.client.post(url, {"decision": "ouvrir"})
        self.filiere.refresh_from_db()
        self.assertEqual(self.filiere.statut, Filiere.OUVERTE)

    @override_settings(FILIERE_DECISION_ROLES=("admin", "enseignant"))
    def test_enseignant_peut_decider_si_autorise(self):
        self.client.force_login(self.ens)
        self.client.post(reverse("filiere_decider", args=[self.filiere.pk]), {"decision": "refuser"})
        self.filiere.refresh_from_db()
        self.assertEqual(self.filiere.statut, Filiere.REFUSEE)

    def test_crud_filiere_reserve_admin(self):
        self.client.force_login(self.etu)
        self.assertEqual(self.client.get(reverse("filiere_create")).status_code, 403)
        self.client.force_login(self.admin)
        r = self.client.post(reverse("filiere_create"), {"nom": "IA", "description": "x"})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Filiere.objects.filter(nom="IA").exists())
        r = self.client.post(reverse("filiere_delete", args=[self.filiere.pk]))
        self.assertFalse(Filiere.objects.filter(pk=self.filiere.pk).exists())
