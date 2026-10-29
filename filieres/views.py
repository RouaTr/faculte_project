from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import AdminRequiredMixin, role_required
from accounts.models import Enseignant, Etudiant, Utilisateur

from .forms import FiliereForm
from .models import DisponibiliteEnseignant, Filiere, VoteEtudiant


def erreur_403(request, exception=None):
    return render(request, "403.html", status=403)


def _annoter_participation(user, filieres):
    """Ajoute `mon_choix` (vote ou disponibilité de l'utilisateur) à chaque filière."""
    filieres = list(filieres)
    ids = [f.pk for f in filieres]
    reponses = {}
    if user.role == Utilisateur.ETUDIANT and hasattr(user, "etudiant"):
        reponses = dict(VoteEtudiant.objects.filter(etudiant=user.etudiant, filiere_id__in=ids)
                        .values_list("filiere_id", "choix"))
    elif user.role == Utilisateur.ENSEIGNANT and hasattr(user, "enseignant"):
        reponses = dict(DisponibiliteEnseignant.objects.filter(enseignant=user.enseignant, filiere_id__in=ids)
                        .values_list("filiere_id", "peut_enseigner"))
    for f in filieres:
        f.mon_choix = reponses.get(f.pk)  # True / False / None (pas encore répondu)
    return filieres


def _retour(request, defaut):
    cible = request.POST.get("next", "")
    if cible and url_has_allowed_host_and_scheme(cible, {request.get_host()}, request.is_secure()):
        return redirect(cible)
    return redirect(defaut)


# --- Tableau de bord ------------------------------------------------------
@login_required
def dashboard(request):
    user = request.user
    if user.role == Utilisateur.ADMIN:
        statuts = dict(Filiere.objects.values_list("statut").annotate(n=Count("pk")))
        ctx = {
            "nb_etudiants": Etudiant.objects.count(),
            "nb_enseignants": Enseignant.objects.count(),
            "nb_en_vote": statuts.get(Filiere.EN_VOTE, 0),
            "nb_ouvertes": statuts.get(Filiere.OUVERTE, 0),
            "nb_refusees": statuts.get(Filiere.REFUSEE, 0),
            "en_vote": Filiere.objects.filter(statut=Filiere.EN_VOTE),
            "recentes": Filiere.objects.exclude(statut=Filiere.EN_VOTE).order_by("-date_decision")[:4],
        }
        return render(request, "dashboard/admin.html", ctx)

    en_vote = _annoter_participation(user, Filiere.objects.filter(statut=Filiere.EN_VOTE))
    ctx = {
        "a_traiter": [f for f in en_vote if f.mon_choix is None],
        "deja_repondu": [f for f in en_vote if f.mon_choix is not None],
        "decisions": _annoter_participation(
            user, Filiere.objects.exclude(statut=Filiere.EN_VOTE).order_by("-date_decision")[:6]),
    }
    return render(request, "dashboard/participant.html", ctx)


# --- Filières (consultation) -----------------------------------------------
class FiliereListView(LoginRequiredMixin, ListView):
    model = Filiere
    paginate_by = 9
    template_name = "filieres/filiere_list.html"

    def get_queryset(self):
        qs = Filiere.objects.all()
        q = self.request.GET.get("q", "").strip()
        statut = self.request.GET.get("statut", "")
        if q:
            qs = qs.filter(Q(nom__icontains=q) | Q(description__icontains=q))
        if statut in dict(Filiere.STATUT_CHOICES):
            qs = qs.filter(statut=statut)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filieres"] = _annoter_participation(self.request.user, ctx["page_obj"].object_list)
        ctx["q"] = self.request.GET.get("q", "").strip()
        ctx["statut_actif"] = self.request.GET.get("statut", "")
        ctx["statuts"] = Filiere.STATUT_CHOICES
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["querystring"] = params.urlencode()
        return ctx


class FiliereDetailView(LoginRequiredMixin, DetailView):
    model = Filiere
    template_name = "filieres/filiere_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        filiere = _annoter_participation(user, [self.object])[0]
        ctx["filiere"] = filiere
        ctx["ma_dispo"] = None
        if user.role == Utilisateur.ENSEIGNANT and hasattr(user, "enseignant"):
            ctx["ma_dispo"] = DisponibiliteEnseignant.objects.filter(enseignant=user.enseignant, filiere=filiere).first()
        if user.role != Utilisateur.ETUDIANT:
            ctx["reponses_enseignants"] = (filiere.disponibilites.select_related("enseignant__utilisateur")
                                           .order_by("-peut_enseigner", "enseignant__utilisateur__last_name"))
        return ctx


# --- Filières (gestion, administrateur) ----------------------------------
class FiliereCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    model = Filiere
    form_class = FiliereForm
    template_name = "filieres/filiere_form.html"
    success_message = "La filière « %(nom)s » est ouverte au vote."

    def get_success_url(self):
        return reverse("filiere_detail", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre"] = "Proposer une filière"
        return ctx


class FiliereUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Filiere
    form_class = FiliereForm
    template_name = "filieres/filiere_form.html"
    success_message = "La filière « %(nom)s » a été mise à jour."

    def get_success_url(self):
        return reverse("filiere_detail", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre"] = f"Modifier {self.object.nom}"
        return ctx


class FiliereDeleteView(AdminRequiredMixin, DeleteView):
    model = Filiere
    template_name = "filieres/filiere_confirm_delete.html"
    success_url = reverse_lazy("filiere_list")

    def form_valid(self, form):
        nom = self.object.nom
        response = super().form_valid(form)
        messages.success(self.request, f"La filière « {nom} » a été supprimée.")
        return response


# --- Actions (POST) -----------------------------------------------------
@require_POST
@role_required(Utilisateur.ETUDIANT)
def voter(request, pk):
    filiere = get_object_or_404(Filiere, pk=pk)
    choix = request.POST.get("choix")
    if not filiere.vote_ouvert:
        messages.error(request, "Le vote est clos pour cette filière.")
    elif choix not in ("oui", "non"):
        messages.error(request, "Choisissez « Oui » ou « Non » pour voter.")
    elif not hasattr(request.user, "etudiant"):
        messages.error(request, "Votre compte n'a pas de profil étudiant. Contactez l'administration.")
    else:
        request.user.etudiant.voter(filiere, choix == "oui")
        messages.success(request, f"Vote enregistré pour {filiere.nom} : {'oui' if choix == 'oui' else 'non'}. "
                                  "Vous pouvez le modifier tant que le vote est ouvert.")
    return _retour(request, reverse("filiere_detail", args=[pk]))


@require_POST
@role_required(Utilisateur.ENSEIGNANT)
def disponibilite(request, pk):
    filiere = get_object_or_404(Filiere, pk=pk)
    reponse = request.POST.get("reponse")
    if not filiere.vote_ouvert:
        messages.error(request, "Le vote est clos pour cette filière.")
    elif reponse not in ("oui", "non"):
        messages.error(request, "Indiquez si vous pouvez ou non enseigner cette filière.")
    elif not hasattr(request.user, "enseignant"):
        messages.error(request, "Votre compte n'a pas de profil enseignant. Contactez l'administration.")
    else:
        commentaire = request.POST.get("commentaire", "").strip()[:200]
        request.user.enseignant.declarer_disponibilite(filiere, reponse == "oui", commentaire)
        messages.success(request, f"Réponse enregistrée pour {filiere.nom}. Vous pouvez la modifier tant que le vote est ouvert.")
    return _retour(request, reverse("filiere_detail", args=[pk]))


@require_POST
@login_required
def decider(request, pk):
    if request.user.role not in settings.FILIERE_DECISION_ROLES:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    filiere = get_object_or_404(Filiere, pk=pk)
    decision = request.POST.get("decision")
    if not filiere.vote_ouvert:
        messages.error(request, "Une décision a déjà été prise pour cette filière.")
    elif decision not in ("ouvrir", "refuser"):
        messages.error(request, "Décision inconnue.")
    else:
        filiere.decider(ouvrir=decision == "ouvrir")
        if decision == "ouvrir":
            messages.success(request, f"La classe {filiere.nom} est ouverte.")
        else:
            messages.success(request, f"La filière {filiere.nom} n'est pas retenue.")
    return redirect("filiere_detail", pk=pk)


@require_POST
@role_required(Utilisateur.ADMIN)
def rouvrir(request, pk):
    filiere = get_object_or_404(Filiere, pk=pk)
    filiere.rouvrir()
    messages.success(request, f"Le vote est de nouveau ouvert pour {filiere.nom}.")
    return redirect("filiere_detail", pk=pk)
