from .models import Conto, IntestazioniConto

class AccountService:
    def get_conti(primary_key):
        return Conto.objects.get(pk=primary_key)

    def get_intestazioni(pk):
        return IntestazioniConto.objects.filter(utente=pk)
    
    def get_conti_utente(pk):
        intestazioni = AccountService.get_intestazioni(pk)
        lista_conti = [] 
        for conto_intestato in intestazioni:
                conto = AccountService.get_conti(conto_intestato.conto.pk)
                lista_conti.append(conto)
        return lista_conti

    from django.utils import timezone


