
from .models import Transazione, PianoDiRisparmio, CategoriaSpesa, ObbiettivoSpesa
from Accounts.models import IntestazioniConto, Conto
from django.utils import timezone
from Users.services import *
from datetime import timedelta
from Accounts.services import *
class BudgetingService: 
    def count_transazioni():
        return Transazione.objects.count()  

    def get_lista_SavingPlan(pk):
        conti = AccountService.get_conti_utente(pk)
        data_corrente = timezone.now().date()  
        lista_piani_risparmio = PianoDiRisparmio.objects.filter(conto__in=conti, data_scadenza__gte=data_corrente)
        
        return lista_piani_risparmio

    def get_transazioni_by_utente(pk):
        transazioni = Transazione.objects.filter(utente = pk)
        return transazioni
    
    def ricalcola_lista_piani_risparmio(pk):
        lista_piani = BudgetingService.get_lista_SavingPlan(pk)
        for piano in lista_piani :
                piano.percentuale_completamento = (piano.conto.saldo / piano.obbiettivo   )*100
                if(piano.percentuale_completamento > 100):
                    piano.percentuale_completamento = 100
                piano.save()
    
    def get_lista_Obbiettivi_Spesa(pk):
        lisa_piani_spesa = ObbiettivoSpesa.objects.filter(utente = pk)
        return lisa_piani_spesa
    
    
    def get_lista_obbiettivi_spesa_by_categoria(pk, cat):
        lisa_piani_spesa = ObbiettivoSpesa.objects.filter(utente = pk, categoria_target = cat)
        return lisa_piani_spesa
    
    
    def get_categorie_utente():
        lista_categorie = CategoriaSpesa.objects.all()
        return lista_categorie
    
    
    def ricacola_percentuale_completamento(request, id):
        utente = UserService.get_utenti_by_user(request.user.id)
        piano = (BudgetingService.get_lista_SavingPlan(utente)).get(pk = id)
        piano.percentuale_completamento = (piano.conto.saldo / piano.obbiettivo )*100
        piano.save()
        return piano.percentuale_completamento
    
    
    def ricalcola_percentuale_completamento_obbiettivoSpesa(request, id):
        utente = UserService.get_utenti_by_user(request.user.id)
        obbiettivo = (BudgetingService.get_lista_Obbiettivi_Spesa(utente)).get(pk = id)
        obbiettivo.percentuale_completamento = (obbiettivo.importo_speso / obbiettivo.importo )*100
        if(obbiettivo.percentuale_completamento > 100):
            obbiettivo.percentuale_completamento = 100
        obbiettivo.save()
        return obbiettivo.percentuale_completamento
    
    
    
    def check_future_transactions(request):
        oggi = timezone.now().date()
        future_transazioni = Transazione.objects.filter(tipo_transazione='futura', data__lte= oggi, utente = UserService.get_utenti_by_user(request.user.pk))
        transazioni_periodiche = Transazione.objects.filter(tipo_transazione='periodica', data__lte= oggi, utente = UserService.get_utenti_by_user(request.user.pk))
        print("ciao" + str(future_transazioni))
        for transazione in future_transazioni:
            if not transazione.eseguita :
                conto = transazione.conto 
                print (conto) 
                if conto.saldo >= (-transazione.importo):
                    conto.saldo += transazione.importo
                    conto.save()
                    transazione.eseguita = True
                    transazione.save()
                else:
                    print(f"Saldo insufficiente per la transazione {transazione.id}")
        
        for transazione in transazioni_periodiche:
            if not transazione.eseguita :
                conto = transazione.conto 
                print (conto) 
                if conto.saldo >= (-transazione.importo):
                    conto.saldo += transazione.importo
                    conto.save()
                    transazione.eseguita = True
                    transazione.save()
                    
                    prima_data = transazione.data
                    data_prossimo_rinnovo = ''
                    data_prossimo_rinnovo_prossimo_rinnovo = ''
                    match transazione.tipo_rinnovo:
                        case 'settimanale': 
                            data_prossimo_rinnovo = prima_data + timedelta(days=7)
                            data_prossimo_rinnovo_prossimo_rinnovo = data_prossimo_rinnovo + timedelta(days=7)
                        case 'mensile': 
                            data_prossimo_rinnovo = prima_data + timedelta(days=30)
                            data_prossimo_rinnovo_prossimo_rinnovo = data_prossimo_rinnovo + timedelta(days=30)
                        case 'semestrale':
                            data_prossimo_rinnovo = prima_data + timedelta(days=180)
                            data_prossimo_rinnovo_prossimo_rinnovo = data_prossimo_rinnovo + timedelta(days=180)
                    
                    Transazione.objects.create(
                        conto=conto,
                        importo= transazione.importo,
                        data=  data_prossimo_rinnovo,
                        descrizione= transazione.descrizione,
                        tipo_transazione= transazione.tipo_transazione,
                        utente=  UserService.get_utenti_by_user(request.user.id),
                        categoria = transazione.categoria, 
                        sotto_categoria = transazione.sotto_categoria, 
                        eseguita = False,
                        prossimo_rinnovo = data_prossimo_rinnovo_prossimo_rinnovo,
                        tipo_rinnovo = transazione.tipo_rinnovo, 
                        )
                else:
                    print(f"Saldo insufficiente per la transazione {transazione.id}")

            
