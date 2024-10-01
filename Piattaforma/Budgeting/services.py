
from .models import Transazione
from Accounts.models import IntestazioniConto, Conto
from django.utils import timezone
from Users.services import *
from datetime import timedelta
class BudgetingService: 
    def count_transazioni():
        return Transazione.objects.count()  

            
    
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

            
