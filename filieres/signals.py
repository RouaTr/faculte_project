from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import DisponibiliteEnseignant, Filiere, VoteEtudiant


@receiver([post_save, post_delete], sender=VoteEtudiant)
@receiver([post_save, post_delete], sender=DisponibiliteEnseignant)
def recalculer_resultats(sender, instance, **kwargs):
    filiere = Filiere.objects.filter(pk=instance.filiere_id).first()
    if filiere:
        filiere.recalculer()
