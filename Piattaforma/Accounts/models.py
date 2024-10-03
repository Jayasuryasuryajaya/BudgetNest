from django.db import models
from Users.models import Utente 

class TipoConto(models.TextChoices):
    CORRENTE = 'corrente', 'Conto Corrente'
    INVESTIMENTO = 'investimento', 'Conto di Investimento'
    RISPARMIO = 'risparmio', 'Conto di Risparmio'
class Conto(models.Model):
    nome = models.CharField(max_length=10)
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tipo = models.CharField(
        max_length=20,
        choices=TipoConto.choices,
        default=TipoConto.CORRENTE,
    )
    def __str__(self):
        return self.nome 
    
    def to_dict(self):
        return {
            'pk': self.pk,
            'saldo': self.saldo,
            'nome': self.nome,
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




