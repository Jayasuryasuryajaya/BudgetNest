from django.db import models
from django.contrib.auth.models import User
import random

class Famiglia(models.Model):
    numero_partecipanti = models.IntegerField(default=1)
    nome_famiglia = models.CharField(max_length=50)
    data_creazione = models.DateField()
    codice = models.CharField(max_length=6, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.codice:
            self.codice = self.generate_unique_code()
        super().save(*args, **kwargs)

    def generate_unique_code(self):
        while True:
           
            code = f"{random.randint(0, 999999):06d}"
            if not Famiglia.objects.filter(codice=code).exists():
                return code

    def __str__(self):
        return self.nome_famiglia

class Sesso(models.TextChoices):
    MASCHIO = 'M', 'Male'
    FEMMINA = 'F', 'Female'
    ALTRO = 'O', 'Other' 

class Utente(models.Model):
    user_profile = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=50)
    nome = models.CharField(max_length=50)
    cognome = models.CharField(max_length=50)
    data_di_nascita = models.DateField()
    indirizzo = models.CharField(max_length=100, null=True, blank=True)
    telefono = models.CharField(max_length=10)
    sesso = models.CharField(
        max_length=1,
        choices=Sesso.choices,
        default=Sesso.MASCHIO,  
    )
    monete_account = models.IntegerField(default=0)
    famiglia = models.ManyToManyField(Famiglia, blank=True) 
    data_registrazione = models.DateField()
    
    def __str__(self):
        return self.username
    
    def to_dict(self):
        return {
            'pk': self.pk,
            'nome': self.nome,
        }