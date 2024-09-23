from django.db import models
from Users.models import Utente
# Create your models here.

class Premio(models.Model):
    percorso_risorsa = models.CharField(max_length=255, null=True, blank=True)
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=50)
    nome = models.CharField(max_length=30)

class AcquistoPremio(models.Model):
    premio = models.ForeignKey(Premio, on_delete=models.CASCADE)
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('premio', 'utente')