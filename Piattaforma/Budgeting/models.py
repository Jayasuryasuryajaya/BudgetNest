from django.apps import AppConfig
from django.db import models
from Users.models import Utente 
from Accounts.models import Conto


class BudgetingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Budgeting'

class CategoriaSpesa(models.Model):
    nome = models.CharField(max_length=50)

class SottoCategoriaSpesa(models.Model):
    categoria_superiore = models.ForeignKey(CategoriaSpesa, on_delete=models.CASCADE)
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE)
    personalizzata = models.BooleanField(default=False)
    data_creazione = models.DateField()
    nome = models.CharField(max_length=50)

class ObbiettivoSpesa(models.Model):
    importo = models.DecimalField(max_digits=10, decimal_places=2)
    percentuale_completamento = models.FloatField(default=0)
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE)
    categoria_target = models.ForeignKey(CategoriaSpesa, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20)
    data_scadenza = models.DateField()
    data_creazione = models.DateField()

class PianoDiRisparmio(models.Model):
    durata = models.CharField(max_length=20)
    obbiettivo = models.DecimalField(max_digits=10, decimal_places=2)
    data_scadenza = models.DateField()
    data_creazione = models.DateField()
    conto = models.ForeignKey(Conto, on_delete=models.CASCADE)
    