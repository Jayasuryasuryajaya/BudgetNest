from django.db import models
from Users.models import Famiglia, Utente
from Budgeting.models import CategoriaSpesa
# Create your models here.
class SfidaPersonale(models.Model):
    nome_sfida = models.CharField(max_length=50)
    conclusa = models.BooleanField(default=False)
    importo = models.DecimalField(max_digits=10, decimal_places=2)
    descrizione = models.TextField()
    premio = models.IntegerField()
    data_scadenza = models.DateField()
    data_creazione = models.DateField()
    data_avvio = models.DateField(null=True, blank=True)
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE)
    categoria_target = models.ForeignKey(CategoriaSpesa, on_delete=models.CASCADE)



class SfidaFamigliare(models.Model):
    sfidante = models.ForeignKey(Utente, related_name='sfidante', on_delete=models.CASCADE)
    sfidato = models.ForeignKey(Utente, related_name='sfidato', on_delete=models.CASCADE)
    conclusa = models.BooleanField(default=False)
    vincitore = models.ForeignKey(Utente, null=True, blank=True, related_name='vincitore', on_delete=models.SET_NULL)
    data_creazione = models.DateField()
    data_scadenza = models.DateField()
    importo_sfidante = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    importo_sfidato = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descrizione = models.TextField(null=True, blank=True)
    categoria_target = models.ForeignKey(CategoriaSpesa, on_delete=models.CASCADE, null=True, blank=True)
    famiglia = models.ForeignKey(Famiglia, on_delete=models.CASCADE, null=True)
    percentuale_sfidante = models.DecimalField(max_digits=10, decimal_places=2, default=50)
    percentuale_sfidato = models.DecimalField(max_digits=10, decimal_places=2, default=50)
