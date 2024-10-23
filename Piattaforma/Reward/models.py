
from django.db import models
from django.utils import timezone
from Users.models import Utente


class Premio(models.Model):
    costo_monete = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tipo = models.CharField(max_length=50)
    nome = models.CharField(max_length=30)
    valore = models.DecimalField(max_digits=10, decimal_places=2, default= 0)

class AcquistoPremio(models.Model):
    premio = models.ForeignKey(Premio, on_delete=models.CASCADE)
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE)
    data_acquisto = models.DateField(default=timezone.now)

    