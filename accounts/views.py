from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import UtilisateurForm
from .mixins import AdminRequiredMixin
from .models import Utilisateur


class UtilisateurListView(AdminRequiredMixin, ListView):
    model = Utilisateur
    paginate_by = 10
    template_name = "accounts/utilisateur_list.html"

    def get_queryset(self):
        qs = Utilisateur.objects.select_related("etudiant", "enseignant")
        q = self.request.GET.get("q", "").strip()
        role = self.request.GET.get("role", "")
        if q:
            qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q)
                           | Q(email__icontains=q) | Q(username__icontains=q)
                           | Q(etudiant__matricule__icontains=q))
        if role in dict(Utilisateur.ROLE_CHOICES):
            qs = qs.filter(role=role)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "").strip()
        ctx["role_actif"] = self.request.GET.get("role", "")
        ctx["roles"] = Utilisateur.ROLE_CHOICES
        ctx["total"] = Utilisateur.objects.count()
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["querystring"] = params.urlencode()
        return ctx


class UtilisateurDetailView(AdminRequiredMixin, DetailView):
    model = Utilisateur
    template_name = "accounts/utilisateur_detail.html"
    context_object_name = "utilisateur"


class _FormKwargsMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["acteur"] = self.request.user
        return kwargs


class UtilisateurCreateView(AdminRequiredMixin, _FormKwargsMixin, SuccessMessageMixin, CreateView):
    model = Utilisateur
    form_class = UtilisateurForm
    template_name = "accounts/utilisateur_form.html"
    success_url = reverse_lazy("utilisateur_list")
    success_message = "Le compte de %(first_name)s %(last_name)s a été créé."

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre"] = "Nouvel utilisateur"
        return ctx


class UtilisateurUpdateView(AdminRequiredMixin, _FormKwargsMixin, SuccessMessageMixin, UpdateView):
    model = Utilisateur
    form_class = UtilisateurForm
    template_name = "accounts/utilisateur_form.html"
    success_url = reverse_lazy("utilisateur_list")
    success_message = "Le compte de %(first_name)s %(last_name)s a été mis à jour."

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["titre"] = f"Modifier {self.object.nom_complet}"
        return ctx


class UtilisateurDeleteView(AdminRequiredMixin, DeleteView):
    model = Utilisateur
    template_name = "accounts/utilisateur_confirm_delete.html"
    success_url = reverse_lazy("utilisateur_list")

    def post(self, request, *args, **kwargs):
        cible = self.get_object()
        if cible.pk == request.user.pk:
            messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
            return redirect("utilisateur_list")
        if cible.role == Utilisateur.ADMIN and Utilisateur.objects.filter(role=Utilisateur.ADMIN).count() <= 1:
            messages.error(request, "Impossible de supprimer le dernier administrateur.")
            return redirect("utilisateur_list")
        nom = cible.nom_complet
        cible.delete()
        messages.success(request, f"Le compte de {nom} a été supprimé.")
        return redirect(self.success_url)
