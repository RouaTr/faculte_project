from django import forms

from .models import Filiere


class FiliereForm(forms.ModelForm):
    class Meta:
        model = Filiere
        fields = ["nom", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 5, "placeholder": "À quoi prépare cette filière ? Quels débouchés ?"})}
        help_texts = {"description": "Visible par les étudiants et les enseignants au moment du vote."}

    def clean_nom(self):
        nom = self.cleaned_data["nom"].strip()
        doublon = Filiere.objects.filter(nom__iexact=nom).exclude(pk=self.instance.pk)
        if doublon.exists():
            raise forms.ValidationError("Une filière porte déjà ce nom.")
        return nom
