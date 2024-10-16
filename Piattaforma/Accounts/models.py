from django.db import models
from Users.models import Utente 

class TipoConto(models.TextChoices):
    CORRENTE = 'corrente', 'Checking Account'
    INVESTIMENTO = 'investimento', 'Investment Account'
    RISPARMIO = 'risparmio', 'Savings Account'
    CASH = 'contante', 'Cash'
class Conto(models.Model):
    nome = models.CharField(max_length=10)
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    liquidita = models.DecimalField(max_digits=10, decimal_places=2, default=saldo)
    tipo = models.CharField(
        max_length=20,
        choices=TipoConto.choices,
        default=TipoConto.CORRENTE,
    )
    condiviso = models.BooleanField(default=False)
    def __str__(self):
        return self.nome 
    
    
    def to_dict(self):
        return {
            'pk': self.pk,
            'saldo': float(self.saldo),
            'nome': self.nome,
            'condiviso': self.condiviso, 
            'tipo' : self.tipo,
        }

class IntestazioniConto(models.Model):
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE)
    conto = models.ForeignKey(Conto, on_delete=models.CASCADE)
    data_intestazione = models.DateField()
    def __str__(self):
        return  f'{self.utente.username} {self.conto.nome} {self.data_intestazione}'

    class Meta:
        unique_together = ('utente', 'conto')


class SaldoTotale(models.Model):
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE)
    saldo_totale = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    data_aggiornamento = models.DateField()
    
    def __str__(self):
        return f"Profilo di {self.utente.username} nel giorno {self.data_aggiornamento}"

class SaldoTotaleInvestimenti(models.Model):
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE)
    saldo_totale = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    data_aggiornamento = models.DateField()
    
    def __str__(self):
        return f"Profilo di {self.utente.username} nel giorno {self.data_aggiornamento}"


class PosizioneAperta(models.Model):
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE)
    saldo_totale = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    saldo_investito = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pmc = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    differenza = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ticker = models.CharField(max_length=10)
    nome_azienda = models.CharField(max_length=50)
    conto = models.ForeignKey(Conto, on_delete=models.CASCADE)
    numero_azioni = models.DecimalField(max_digits=10, decimal_places=2, default=0)
 




