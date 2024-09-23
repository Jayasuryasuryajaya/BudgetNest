from django.db import models


class Famiglia(models.Model):
    numero_partecipanti = models.IntegerField(default=1)
    nome_famiglia = models.CharField(max_length=50)
    data_creazione = models.DateField()

class Utente(models.Model):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=50)
    nome = models.CharField(max_length=50)
    cognome = models.CharField(max_length=50)
    data_di_nascita = models.DateField()
    indirizzo = models.CharField(max_length=100, null=True, blank=True)
    telefono = models.CharField(max_length=10)
    sesso = models.CharField(max_length=1)
    monete_account = models.IntegerField(default=0)
    famiglia = models.ForeignKey(Famiglia, null=True, blank=True, on_delete=models.SET_NULL)
    data_registrazione = models.DateField()

