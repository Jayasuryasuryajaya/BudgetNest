
from .models import Transazione, PianoDiRisparmio, CategoriaSpesa, ObbiettivoSpesa, SottoCategoriaSpesa
from Accounts.models import IntestazioniConto, Conto
from django.utils import timezone
from Users.services import *
from datetime import timedelta
from Accounts.services import *
from Challenges.services import *
from django.db.models import Sum
from .models import Transazione
class BudgetingService: 
    def count_transazioni():
        return Transazione.objects.count()  

    def get_lista_SavingPlan_by_conto(conti):
        data_corrente = timezone.now().date()  
        lista_piani_risparmio = PianoDiRisparmio.objects.filter(conto__in=conti, data_scadenza__gte=data_corrente)
        return lista_piani_risparmio
    
    def get_lista_SavingPlan(pk):
        conti = AccountService.get_conti_utente(pk)
        data_corrente = timezone.now().date()  
        lista_piani_risparmio = PianoDiRisparmio.objects.filter(conto__in=conti, data_scadenza__gte=data_corrente)
        
        return lista_piani_risparmio
    
    def get_transazioni_by_conti(conti):
        data_corrente = timezone.now().date()  
        lista_transazioni = Transazione.objects.filter(conto__in=conti, data__lte=data_corrente, eseguita = True)
        return lista_transazioni
    
    def get_lista_SavingPlan_byConto(conto_id):
        data_corrente = timezone.now().date()
        lista_piani_risparmio = PianoDiRisparmio.objects.filter(
            conto_id=conto_id,
            data_scadenza__gte=data_corrente
        )
    
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
        oggi = timezone.now().date()
        lista_piani_spesa = ObbiettivoSpesa.objects.filter(utente=pk, data_scadenza__gte=oggi)
        return lista_piani_spesa
    
    def get_lista_obbiettivi_spesa_by_categoria(pk, cat):
        lisa_piani_spesa = ObbiettivoSpesa.objects.filter(utente = pk, categoria_target = cat)
        return lisa_piani_spesa
    
    
    def get_categorie_utente():
        lista_categorie = CategoriaSpesa.objects.all()
        return lista_categorie
    
    def get_sotto_categorie_utente(utente):
        lista_sotto_categorie = SottoCategoriaSpesa.objects.filter(utente = utente)
        return lista_sotto_categorie
    
    def ricalcola_percentuale_completamento_pianoRisparmio(request, id):
        utente = UserService.get_utenti_by_user(request.user.id)
        piano = (BudgetingService.get_lista_SavingPlan(utente)).get(pk = id)
        piano.percentuale_completamento = (piano.conto.saldo / piano.obbiettivo )*100
        if(piano.percentuale_completamento > 100):
            piano.percentuale_completamento = 100
        if(piano.percentuale_completamento < 0):
            piano.percentuale_completamento = 0
        piano.save()
        return piano.percentuale_completamento
    
   
    def aggiorna_saldo_totale_dopo_inserimento(utente, data_transazione, importo):
        saldo_records = SaldoTotale.objects.filter(utente=utente, data_aggiornamento__gte=data_transazione)
        for record in saldo_records:
            record.saldo_totale += importo
            record.save()
   
    def ricalcola_percentuale_completamento_obbiettivoSpesa(request, id):
        
        utente = UserService.get_utenti_by_user(request.user.id)
        obbiettivo = (BudgetingService.get_lista_Obbiettivi_Spesa(utente)).get(pk = id)
        obbiettivo.percentuale_completamento = (obbiettivo.importo_speso / obbiettivo.importo )*100
        if(obbiettivo.percentuale_completamento > 100):
            obbiettivo.percentuale_completamento = 100
        if(obbiettivo.percentuale_completamento <= 0):
            obbiettivo.percentuale_completamento = 0
        obbiettivo.save()
        return obbiettivo.percentuale_completamento
    
   
    def get_spese_per_categoria_ultimo_mese(utente):
        un_mese_fa = timezone.now() - timedelta(days=30)
        spese_per_categoria = (
        Transazione.objects.filter(
            utente=utente, 
            eseguita=True, 
            importo__lt=0,  # Filtro per importo negativo
            categoria__isnull=False ,
            data__gte= un_mese_fa# Solo le transazioni con una categoria assegnata
        )
        .values('categoria')  # Supponendo che tu abbia un campo 'nome' nella categoria
        .annotate(totale=Sum('importo'))  # Somma degli importi per categoria
    )
       

        
        categorie = []
        importi = []
        for spesa in spese_per_categoria:
            categoria = CategoriaSpesa.objects.get(pk = spesa['categoria'])
            
            cat = categoria.nome
                
            categorie.append(cat)
            importi.append(float(spesa['totale']))

        return categorie, importi
    
    def get_spese_per_categoria(utente):
        spese_per_categoria = (
        Transazione.objects.filter(
            utente=utente, 
            eseguita=True, 
            importo__lt=0,  # Filtro per importo negativo
            categoria__isnull=False  # Solo le transazioni con una categoria assegnata
        )
        .values('categoria')  # Supponendo che tu abbia un campo 'nome' nella categoria
        .annotate(totale=Sum('importo'))  # Somma degli importi per categoria
    )
       

        
        categorie = []
        importi = []
        for spesa in spese_per_categoria:
            categoria = CategoriaSpesa.objects.get(pk = spesa['categoria'])
            
            cat = categoria.nome
                
            categorie.append(cat)
            importi.append(float(spesa['totale']))

        return categorie, importi

    
    
    def check_future_transactions(request):
        utente = UserService.get_utenti_by_user(request.user.id)
        oggi = timezone.now().date()
        future_transazioni = Transazione.objects.filter(tipo_transazione='futura', data__lte= oggi, utente = UserService.get_utenti_by_user(request.user.pk))
        transazioni_periodiche = Transazione.objects.filter(tipo_transazione='periodica', data__lte= oggi, utente = UserService.get_utenti_by_user(request.user.pk))
        obbiettivi_spesa = BudgetingService.get_lista_Obbiettivi_Spesa(utente)
    
        for transazione in future_transazioni:
            if not transazione.eseguita :
                conto = transazione.conto 
              
                if conto.saldo >= (-transazione.importo):
                    conto.saldo += transazione.importo
                    conto.save()
                    transazione.eseguita = True
                    transazione.save()
                    BudgetingService.ricalcola_lista_piani_risparmio(utente)
                    BudgetingService.aggiorna_saldo_totale_dopo_inserimento(utente, transazione.data, transazione.importo)
                    ChallengeService.aggiorna_sfida(utente,transazione.categoria,transazione.importo, transazione.data.strftime('%Y-%m-%d'))
                    if any(transazione.categoria == obbiettivo.categoria_target for obbiettivo in obbiettivi_spesa):
                        obbiettivi_spesa_filtrati = obbiettivi_spesa.filter(
                            categoria_target=transazione.categoria,
                            data_creazione__lte=transazione.data,  # data_creazione <= data_esecuzione
                            data_scadenza__gte=transazione.data   # data_scadenza >= data_esecuzione
                        )
                        for obbiettivo in obbiettivi_spesa_filtrati:
                            obbiettivo.importo_speso -= transazione.importo
                            obbiettivo.save()
                            BudgetingService.ricalcola_percentuale_completamento_obbiettivoSpesa(request, obbiettivo.pk)
                            
                            
                        
                    
                    
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
                    
                    BudgetingService.ricalcola_lista_piani_risparmio(utente)
                    BudgetingService.aggiorna_saldo_totale_dopo_inserimento(utente, transazione.data, transazione.importo)
                    ChallengeService.aggiorna_sfida(utente,transazione.categoria,transazione.importo, transazione.data.strftime('%Y-%m-%d'))
                    if any(transazione.categoria == obbiettivo.categoria_target for obbiettivo in obbiettivi_spesa):
                        obbiettivi_spesa_filtrati = obbiettivi_spesa.filter(
                            categoria_target=transazione.categoria,
                            data_creazione__lte=transazione.data,  # data_creazione <= data_esecuzione
                            data_scadenza__gte=transazione.data   # data_scadenza >= data_esecuzione
                        )
                        for obbiettivo in obbiettivi_spesa_filtrati:
                            obbiettivo.importo_speso -= transazione.importo
                            obbiettivo.save()
                            BudgetingService.ricalcola_percentuale_completamento_obbiettivoSpesa(request,obbiettivo.pk)
                            
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

            
