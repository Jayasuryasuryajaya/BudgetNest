from .models import Conto, IntestazioniConto, SaldoTotale
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

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
    
    


    def calcola_saldo_totale(utente):
    
        conti = AccountService.get_conti_utente(utente)
        totale = sum(conto.saldo for conto in conti)  # Calcola il saldo totale

        # Controlla se esiste già un SaldoTotale per l'utente con la data di oggi
        data_aggiornamento = timezone.now().date()
        try:
            saldo = SaldoTotale.objects.get(utente=utente, data_aggiornamento=data_aggiornamento)
            saldo.saldo_totale = totale
            saldo.save()
             # Puoi anche gestire questa situazione come preferisci
        except ObjectDoesNotExist:
            # Se non esiste, crea un nuovo oggetto SaldoTotale
            SaldoTotale.objects.create(
                utente=utente,
                saldo_totale=totale,  # Assicurati che il campo si chiami 'saldo_totale'
                data_aggiornamento=data_aggiornamento
            )
            print("Nuovo saldo totale creato.")

        
    def modifica_saldo_totale(utente, transazione):
        riga_saldo = SaldoTotale.objects.get(utente = utente, data_aggiornamento = timezone.now().date() )  
        riga_saldo.saldo_totale += transazione
        riga_saldo.save()

    from django.utils import timezone

    

