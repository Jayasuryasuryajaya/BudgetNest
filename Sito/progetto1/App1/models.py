from django.db import models

# Create your models here.
class utente(models.Model):
        nome = models.CharField(max_length=150)
        password = models.TextField()
        cognome = models.CharField(max_length=150)
        descrizione = models.CharField(max_length=150) 