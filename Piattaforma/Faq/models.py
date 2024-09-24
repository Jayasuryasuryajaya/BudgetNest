from collections.abc import Iterable
from django.db import models


class Faq(models.Model):
    Domanda = models.CharField(max_length=255, blank=True)
    Risposta = models.CharField(max_length=255,  blank=True)
    
    def __str__(self):
        return self.Domanda
    