from django.apps import AppConfig
from django.db import models
from Users.models import Utente 
from Accounts.models import Conto


class BudgetingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Budgeting'

class CategoriaSpesa(models.Model):
    nome = models.CharField(max_length=50)
    def __str__(self):
        return self.nome
    def to_dict(self):
        return {
            'nome': self.nome,
         
        }

class SottoCategoriaSpesa(models.Model):
    categoria_superiore = models.ForeignKey(CategoriaSpesa, on_delete=models.CASCADE,)
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE, null= True)
    personalizzata = models.BooleanField(default=False)
    data_creazione = models.DateField()
    nome = models.CharField(max_length=50, null= True)
    
    def __str__(self):
        return self.categoria_superiore.nome + ' -> ' + str(self.nome);

class ObbiettivoSpesa(models.Model):
    TIPO_SCELTE = [
        ('mensile', 'Mensile'),
        ('trimestrale', 'Trimestrale'),
        ('semestrale', 'Semestrale'),
        ('annuale', 'Annuale'),
    ]
    
    importo_speso = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    importo = models.DecimalField(max_digits=10, decimal_places=2)
    percentuale_completamento = models.FloatField(default=0)
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE)
    categoria_target = models.ForeignKey(CategoriaSpesa, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_SCELTE)
    data_scadenza = models.DateField()
    data_creazione = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo} - {self.importo}"


class PianoDiRisparmio(models.Model):
    durata = models.CharField(max_length=20)
    obbiettivo = models.DecimalField(max_digits=10, decimal_places=2)
    data_scadenza = models.DateField()
    data_creazione = models.DateField()
    conto = models.ForeignKey(Conto, on_delete=models.CASCADE)
    percentuale_completamento = models.DecimalField(max_digits=10, decimal_places=2, default = 0)
    
class CategoriaTransazione(models.TextChoices):
    DELEGATA = 'delegata', 'Transazione Delegata'
    SINGOLA = 'singola', 'Transazione Singola'
    PERIODICA = 'periodica', 'Transazione Periodica'
    FUTURA = 'futura', 'Transazione Futura'
    TRASFERIMENTO = 'trasferimento', 'Trasferimento tra Conti'
    INVESTIMENTO = 'investimento', 'Transazione di Investimento'
    
class TipoRinnovo(models.TextChoices):
    SETTIMANALE = 'settimanale', 'Rinnovo Settimanale'
    MENSILE = 'mensile', 'Rinnovo Mensile'
    SEMESTRALE = 'semestrale', 'Rinnovo Semestrale'
    NESSUNO = 'nessuno' , 'Nessun Rinnovo'
    
    
class Transazione(models.Model):
    importo = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField()
    mostra = models.BooleanField(default=True)
    eseguita = models.BooleanField(default=True)
    tipo_transazione = models.CharField(
        max_length=20,
        choices=CategoriaTransazione.choices,
        default=CategoriaTransazione.SINGOLA,  
    )
    prossimo_rinnovo = models.DateField(null=True, blank=True)
    ticker = models.CharField(max_length=10, null=True, blank=True)
    prezzo_azione = models.FloatField(null=True, blank=True)
    numero_azioni = models.FloatField(null=True, blank=True)
    borsa = models.CharField(max_length=50, null=True, blank=True)
    valuta = models.CharField(max_length=3, null=True, blank=True)
    conto = models.ForeignKey(Conto, on_delete=models.CASCADE,  related_name='conto_partenza')
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE)
    categoria = models.ForeignKey(CategoriaSpesa, null=True, blank=True, on_delete=models.SET_NULL)
    sotto_categoria = models.ForeignKey(SottoCategoriaSpesa, null=True, blank=True, on_delete=models.SET_NULL)
    mittente_delega = models.ForeignKey(Utente, null=True, blank=True, related_name='delegante', on_delete=models.SET_NULL)
    accetta_delega = models.BooleanField(null=True, blank=True)
    descrizione = models.TextField(null=True, blank=True)
    tipo_rinnovo = models.CharField(
        max_length=20,
        choices=TipoRinnovo.choices,
        default=TipoRinnovo.NESSUNO,
        null=True,
        blank=True
    )
    conto_arrivo = models.ForeignKey(Conto, on_delete=models.CASCADE, null= True, blank=True,  related_name='conto_arrivo')
    

    