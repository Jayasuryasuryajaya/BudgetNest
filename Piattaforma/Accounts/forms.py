from django.forms import ModelForm
from Accounts.models import Conto, TipoConto
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from .services import *
from Users.services import *


class NuovoConto(ModelForm):
    saldo = forms.DecimalField(
            widget=forms.NumberInput(attrs={
                'placeholder': 'Enter start amount', 
                'min': '0',  
                'step': '0.01' ,
                'class': 'form-control',
            })
        )
    tipo = forms.ChoiceField(
        choices= TipoConto,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    class Meta:
        model = Conto
        fields = ["nome", "tipo", "saldo"]
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Enter bank name', 
                                           'class': 'form-control',
                                           }),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None) 
        super(NuovoConto, self).__init__(*args, **kwargs)


    def clean_nome(self):
        nome = self.cleaned_data.get("nome")
        if self.request:
            conti = AccountService.get_conti_utente(UserService.get_utenti_by_user(self.request.user.pk))
            if any(conto.nome.lower() == nome for conto in conti):
                raise ValidationError("This account name is already taken.")
        
        return nome


class NuovoContoFamiglia(ModelForm):
    saldo = forms.DecimalField(
            widget=forms.NumberInput(attrs={
                'placeholder': 'Enter start amount', 
                'min': '0',  
                'step': '0.01' ,
                'class': 'form-control',
            })
        )

    class Meta:
        model = Conto
        fields = ["nome", "saldo"]
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Enter bank name', 
                                           'class': 'form-control',
                                           }),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None) 
        super(NuovoContoFamiglia, self).__init__(*args, **kwargs)


    def clean_nome(self):
        nome = self.cleaned_data.get("nome")
        if self.request:
            conti = AccountService.get_conti_utente(UserService.get_utenti_by_user(self.request.user.pk))
            if any(conto.nome.lower() == nome for conto in conti):
                raise ValidationError("This account name is already taken.")
        return nome
       
    
    
   