from decimal import Decimal
from django.conf import settings
from Users.models import Utente
from .models import Conto, IntestazioniConto, SaldoTotale, TipoConto, SaldoTotaleInvestimenti, PosizioneAperta
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
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
    
    def get_conti_investimento_utente(pk):
        intestazioni = AccountService.get_intestazioni(pk)
        lista_conti = [] 
        for conto_intestato in intestazioni:
                conto = Conto.objects.filter(pk=conto_intestato.conto.pk, tipo= TipoConto.INVESTIMENTO)
                for c in conto:
                    lista_conti.append(c)
        return lista_conti
    
    
    def get_family_members(famiglia):
        family_members = Utente.objects.filter(famiglia=famiglia)
        return family_members

    
    def get_family_accounts(famiglia):
      
        family_members = Utente.objects.filter(famiglia=famiglia)
       
        accounts = IntestazioniConto.objects.filter(utente__in=family_members)

        
        accounts_grouped = accounts.values('conto').annotate(num_utenti=Count('utente'))
        
        
        
        accounts_with_all_members = accounts_grouped.filter(num_utenti=len(family_members))
       
        
        
        final_accounts = Conto.objects.filter(pk__in=accounts_with_all_members.values('conto')).distinct()
   
        return list(final_accounts)
    
  

    def calcola_saldo_totale(utente):
    
        conti = AccountService.get_conti_utente(utente)
        totale = sum(conto.saldo for conto in conti)  
        data_aggiornamento = timezone.now().date()
        try:
            
            saldo = SaldoTotale.objects.get(utente=utente, data_aggiornamento=data_aggiornamento)
            saldo.saldo_totale = totale
            saldo.save()
            
        except ObjectDoesNotExist:
           
            SaldoTotale.objects.create(
                utente=utente,
                saldo_totale=totale, 
                data_aggiornamento=data_aggiornamento
            )
          

        
    def modifica_saldo_totale(utente, transazione):
        riga_saldo = SaldoTotale.objects.get(utente = utente, data_aggiornamento = timezone.now().date() )  
        riga_saldo.saldo_totale += transazione
        riga_saldo.save()


    def calcola_saldo_totale_investimenti(utente):
        conti = AccountService.get_conti_investimento_utente(utente)
        totale = sum(conto.saldo for conto in conti)  
        data_aggiornamento = timezone.now().date()
        try:
            saldo = SaldoTotaleInvestimenti.objects.get(utente=utente, data_aggiornamento=data_aggiornamento)
            saldo.saldo_totale = totale
            saldo.save()
           
        except ObjectDoesNotExist:
           
            SaldoTotaleInvestimenti.objects.create(
                utente=utente,
                saldo_totale=totale,  
                data_aggiornamento=data_aggiornamento
            )
            print("Nuovo saldo totale creato.")
    
    
        
    def modifica_saldo_totale_investimenti(utente, transazione):
        riga_saldo = SaldoTotaleInvestimenti.objects.get(utente = utente, data_aggiornamento = timezone.now().date() )  
        riga_saldo.saldo_totale += transazione
        riga_saldo.save()


    def get_posizioni(utente):
        p = PosizioneAperta.objects.filter(utente = utente)
        return p
        
    def calcola_pmc(posizione):
        posizione.pmc = posizione.saldo_investito / posizione.numero_azioni
        posizione.save()
        return
    
    def registra_posizione_investimento(utente, conto, ticker, numero_azioni, prezzo_azione, nome_azienda):
        
        posizioni = AccountService.get_posizioni(utente= utente)
        
        for posizione in posizioni:
            if(posizione.conto == conto and posizione.utente == utente and posizione.ticker == ticker):
                posizione.numero_azioni += Decimal(numero_azioni)
                posizione.saldo_investito += Decimal(numero_azioni*prezzo_azione)
                posizione.saldo_totale += Decimal(numero_azioni*prezzo_azione)
                posizione.save()
                AccountService.calcola_pmc(posizione)
                return
       
        PosizioneAperta.objects.create(
            utente = utente,
            saldo_totale = (numero_azioni*prezzo_azione),
            saldo_investito = (numero_azioni*prezzo_azione),
            pmc = prezzo_azione,
            differenza = 0,
            ticker = ticker,
            nome_azienda = nome_azienda,
            conto = conto,
            numero_azioni = numero_azioni
            )
        return

    def registra_posizione_vendita(utente, conto, ticker, numero_azioni, prezzo_azione,pmc):
        posizioni = AccountService.get_posizioni(utente=utente)
        
        for posizione in posizioni:
           
            if posizione.conto == conto and posizione.utente == utente and posizione.ticker == ticker:
                if posizione.numero_azioni < numero_azioni:
                    raise ValueError("Non puoi vendere più azioni di quelle possedute.")  
                
                posizione.numero_azioni -= Decimal(numero_azioni)
                posizione.save()
                posizione.saldo_totale = Decimal(posizione.numero_azioni * prezzo_azione)
                posizione.saldo_investito -= Decimal(numero_azioni * pmc)
                posizione.save()
                posizione.differenza += posizione.saldo_totale - posizione.saldo_investito
                posizione.save()
                
                totale_posizioni = 0
                conto.liquidita += Decimal(numero_azioni * prezzo_azione)
                posizioni = PosizioneAperta.objects.filter(conto = conto)
                for posizione in posizioni:
                        totale_posizioni += posizione.saldo_totale
                conto.saldo = conto.liquidita + totale_posizioni
                conto.save()
                
                print(posizione.numero_azioni)
                if(posizione.numero_azioni == 0):
                    posizione.delete()
                    
                
                return
        
        
        raise ValueError("Posizione non trovata per la vendita.")
