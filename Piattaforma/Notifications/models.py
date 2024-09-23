from django.db import models
from Users.models import Utente
# Create your models here.
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
    rif_transazione = models.BigIntegerField(null=True, blank=True)
    rif_sfida = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('id_notifica',)

class NotificaSistema(models.Model):
    id_notifica = models.ForeignKey(Notifica, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20)
    rif_piano_risparmio = models.IntegerField(null=True, blank=True)
    rif_obbiettivo_spesa = models.IntegerField(null=True, blank=True)
    rif_sfida_personale = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('id_notifica',)