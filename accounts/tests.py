from django.test import TestCase
from django.urls import reverse

from accounts.models import Enseignant, Etudiant, Utilisateur


class UtilisateurCrudTests(TestCase):
    def setUp(self):
        self.admin = Utilisateur.objects.create_user("boss", password="x-secret-123", role="admin",
                                                     first_name="Boss", last_name="Admin", email="boss@t.tn")
        self.client.force_login(self.admin)

    def donnees(self, **extra):
        base = {"first_name": "Amel", "last_name": "Ben", "email": "amel@t.tn", "username": "amel",
                "role": "etudiant", "password1": "Motdepasse-2026", "password2": "Motdepasse-2026",
                "matricule": "ETU-1", "niveau": "3"}
        base.update(extra)
        return base

    def test_non_admin_refuse(self):
        etu = Utilisateur.objects.create_user("e", password="x", role="etudiant")
        self.client.force_login(etu)
        self.assertEqual(self.client.get(reverse("utilisateur_list")).status_code, 403)

    def test_creer_etudiant_avec_profil(self):
        r = self.client.post(reverse("utilisateur_create"), self.donnees())
        self.assertEqual(r.status_code, 302)
        user = Utilisateur.objects.get(username="amel")
        self.assertEqual(user.etudiant.matricule, "ETU-1")
        self.assertTrue(user.check_password("Motdepasse-2026"))

    def test_creer_enseignant_avec_profil(self):
        self.client.post(reverse("utilisateur_create"), self.donnees(
            username="prof", email="p@t.tn", role="enseignant", specialite="Cloud", grade="professeur"))
        self.assertEqual(Utilisateur.objects.get(username="prof").enseignant.specialite, "Cloud")

    def test_profil_obligatoire_selon_role(self):
        r = self.client.post(reverse("utilisateur_create"), self.donnees(matricule="", niveau=""))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Utilisateur.objects.filter(username="amel").exists())

    def test_matricule_et_email_uniques(self):
        self.client.post(reverse("utilisateur_create"), self.donnees())
        r = self.client.post(reverse("utilisateur_create"), self.donnees(username="autre"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Utilisateur.objects.filter(username="autre").count(), 0)

    def test_modifier_sans_changer_le_mot_de_passe_ni_le_role(self):
        self.client.post(reverse("utilisateur_create"), self.donnees())
        user = Utilisateur.objects.get(username="amel")
        r = self.client.post(reverse("utilisateur_update", args=[user.pk]), {
            "first_name": "Amel", "last_name": "Nouveau", "email": "amel@t.tn", "username": "amel",
            "role": "admin", "is_active": "on", "matricule": "ETU-1", "niveau": "4"})
        self.assertEqual(r.status_code, 302)
        user.refresh_from_db()
        self.assertEqual((user.last_name, user.role, user.etudiant.niveau), ("Nouveau", "etudiant", "4"))
        self.assertTrue(user.check_password("Motdepasse-2026"))

    def test_supprimer(self):
        self.client.post(reverse("utilisateur_create"), self.donnees())
        user = Utilisateur.objects.get(username="amel")
        self.client.post(reverse("utilisateur_delete", args=[user.pk]))
        self.assertFalse(Utilisateur.objects.filter(pk=user.pk).exists())
        self.assertFalse(Etudiant.objects.filter(matricule="ETU-1").exists())

    def test_ne_peut_pas_se_supprimer_soi_meme(self):
        self.client.post(reverse("utilisateur_delete", args=[self.admin.pk]))
        self.assertTrue(Utilisateur.objects.filter(pk=self.admin.pk).exists())

    def test_recherche_et_filtre(self):
        self.client.post(reverse("utilisateur_create"), self.donnees())
        r = self.client.get(reverse("utilisateur_list"), {"q": "amel", "role": "etudiant"})
        self.assertContains(r, "Amel Ben")
        r = self.client.get(reverse("utilisateur_list"), {"role": "enseignant"})
        self.assertNotContains(r, "Amel Ben")
