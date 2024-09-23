from django.db import models
from Users.models import Utente 
from Budgeting.models import CategoriaSpesa,SottoCategoriaSpesa,ObbiettivoSpesa,PianoDiRisparmio

class Conto(models.Model):
    nome = models.CharField(max_length=50)
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tipo = models.CharField(max_length=20)

class IntestazioniConto(models.Model):
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE)
    conto = models.ForeignKey(Conto, on_delete=models.CASCADE)
    data_intestazione = models.DateField()

    class Meta:
        unique_together = ('utente', 'conto')



class Transazione(models.Model):
    importo = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField()
    mostra = models.BooleanField(default=True)
    tipo = models.CharField(max_length=20)
    prossimo_rinnovo = models.DateField(null=True, blank=True)
    ticker = models.CharField(max_length=10, null=True, blank=True)
    prezzo_azione = models.FloatField(null=True, blank=True)
    numero_azioni = models.FloatField(null=True, blank=True)
    borsa = models.CharField(max_length=50, null=True, blank=True)
    valuta = models.CharField(max_length=3, null=True, blank=True)
    conto = models.ForeignKey(Conto, on_delete=models.CASCADE)
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE)
    categoria = models.ForeignKey(CategoriaSpesa, null=True, blank=True, on_delete=models.SET_NULL)
    sotto_categoria = models.ForeignKey(SottoCategoriaSpesa, null=True, blank=True, on_delete=models.SET_NULL)
    mittente_delega = models.ForeignKey(Utente, null=True, blank=True, related_name='delegante', on_delete=models.SET_NULL)
    accetta_delega = models.BooleanField(null=True, blank=True)
    descrizione = models.TextField(null=True, blank=True)
    tipo_rinnovo = models.CharField(max_length=20, null=True, blank=True)
    
