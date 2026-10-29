# Choix des filières — plateforme de vote pour une faculté

Les étudiants votent **oui / non** pour l'ouverture d'une nouvelle filière (Cloud, par exemple).
Les enseignants indiquent s'ils **peuvent l'enseigner**. La plateforme calcule le pourcentage de oui et le
nombre d'enseignants disponibles, puis la faculté décide d'ouvrir la classe ou non.
Un **CRUD complet des utilisateurs** est réservé à l'administrateur.

## Démarrage rapide

```bash
python -m venv venv
source venv/bin/activate          # Windows : venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo        # comptes et filières de démonstration (facultatif)
python manage.py runserver
```

Ouvrez http://127.0.0.1:8000. Comptes de démonstration (mot de passe `demo12345`) :
`admin`, `etudiant1` … `etudiant12`, `enseignant1` … `enseignant5`.
Sans les données de démonstration, créez l'administrateur avec `python manage.py createsuperuser`.

Tests : `python manage.py test`

## Modèle de données (diagramme de classes)

| Classe | Rôle |
|---|---|
| `Utilisateur` | Compte unique, attribut `role` : `admin`, `enseignant` ou `etudiant` |
| `Etudiant`, `Enseignant` | Profils rattachés à `Utilisateur` (matricule/niveau, spécialité/grade) |
| `Filiere` | Nom, description, `nb_votes_oui`, `nb_votes_non`, `pourcentage_oui`, `nb_enseignants_disponibles`, `statut` |
| `VoteEtudiant` | Table d'association Etudiant 0..* – 0..* Filiere (un seul vote par étudiant et par filière) |
| `DisponibiliteEnseignant` | Table d'association Enseignant 0..* – 0..* Filiere (une seule réponse par enseignant et par filière) |

Les compteurs de `Filiere` sont recalculés automatiquement à chaque vote, changement de vote ou suppression
d'un compte (`filieres/signals.py`).

## Règles métier (config/settings.py)

```python
FILIERE_SEUIL_POURCENTAGE = 60          # % de oui minimum parmi les votants
FILIERE_MIN_ENSEIGNANTS = 2             # enseignants disponibles minimum
FILIERE_DECISION_ROLES = ("admin",)     # ajoutez "enseignant" pour les laisser décider
```

La plateforme **recommande** l'ouverture quand les deux conditions sont réunies ; la personne qui décide
garde le dernier mot (boutons « Ouvrir la classe » / « Ne pas la retenir »). L'administrateur peut rouvrir un vote.

## Droits par rôle

| | Étudiant | Enseignant | Administrateur |
|---|---|---|---|
| Voter oui / non (modifiable tant que le vote est ouvert) | ✔ | | |
| Indiquer sa disponibilité + commentaire | | ✔ | |
| Voir les résultats | après la décision | ✔ | ✔ |
| Décider d'ouvrir la classe | | selon réglage | ✔ |
| CRUD filières et utilisateurs | | | ✔ |

## Structure

```
config/      réglages, URLs
accounts/    Utilisateur, profils, CRUD utilisateurs
filieres/    Filiere, votes, disponibilités, décision, tableaux de bord
templates/   pages et composants
static/      style.css, app.js
```

## Mise en production

Définissez `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0` et `DJANGO_ALLOWED_HOSTS`, puis `python manage.py collectstatic`
et servez les fichiers statiques (WhiteNoise ou serveur web). Passez de SQLite à PostgreSQL dans `DATABASES`.
