from django.db import models
from Users.models import Utente
from Challenges.models import SfidaFamigliare, SfidaPersonale
from Budgeting.models import Transazione
from Budgeting.models import ObbiettivoSpesa,PianoDiRisparmio

class Notifica(models.Model):
    contenuto = models.TextField()
    destinatario = models.ForeignKey(Utente, on_delete=models.CASCADE)
    provenienza = models.CharField(max_length=50)
    data_notifica = models.DateField()
    letta = models.BooleanField(default=False)
    data_lettura = models.DateField(null=True, blank=True)


class NotificaFamiglia(models.Model):
    id_notifica = models.ForeignKey(Notifica, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20)
    rif_transazione = models.ForeignKey(Transazione, on_delete=models.CASCADE)
    rif_sfida = models.ForeignKey(SfidaFamigliare, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('id_notifica',)

class NotificaSistema(models.Model):
    id_notifica = models.ForeignKey(Notifica, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20)
    rif_piano_risparmio = models.ForeignKey(PianoDiRisparmio, on_delete=models.CASCADE)
    rif_obbiettivo_spesa = models.ForeignKey(ObbiettivoSpesa, on_delete=models.CASCADE)
    rif_sfida_personale = models.ForeignKey(SfidaPersonale, on_delete=models.CASCADE)


    class Meta:
        unique_together = ('id_notifica',)