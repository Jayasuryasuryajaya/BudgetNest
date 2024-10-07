from django.shortcuts import render
from .services import *
from django.contrib.auth.decorators import login_required
from .services import AccountService
from Users.services import *
from .forms import *
from django.http import JsonResponse
from django.utils import timezone  
from datetime import date
from Budgeting.forms import *
from django.template.loader import render_to_string
from Budgeting.services import *
from datetime import timedelta
import json
from django.http import JsonResponse
from decimal import Decimal


@login_required
def dashboard_utente(request):
    return render(request, 'dashboard/dashboard.html')

@login_required
def personal_section(request):
    BudgetingService.check_future_transactions(request)
    utente = UserService.get_utenti_by_user(request.user.pk)
    AccountService.calcola_saldo_totale(utente)
    form = NuovoConto()
    formTransazione = NuovaTransazioneForm(utente=request.user)
    conti = AccountService.get_conti_utente(utente.pk)
    formSavingPlan = NuovoPianoRisparmo(utente=request.user)
    formObbiettivoSpesa = ObbiettivoSpesaForm()
    lista_piani_risparmio = BudgetingService.get_lista_SavingPlan(utente)
    lista_obbiettivi_spesa = BudgetingService.get_lista_Obbiettivi_Spesa(utente)
    lista_transazioni = BudgetingService.get_transazioni_by_utente(utente).filter(eseguita=True).order_by('-data')
    saldo_data = SaldoTotale.objects.filter(utente=utente).order_by('data_aggiornamento')


    labels = [str(saldo.data_aggiornamento) for saldo in saldo_data]  # Date per l'asse X
    data = [saldo.saldo_totale for saldo in saldo_data]  # Saldi per l'asse Y

    conti_data = [
                {
                    'id': conto.id,
                    'nome': conto.nome,
                    'tipo': conto.tipo,
                    'saldo': float(conto.saldo),
                }
                for conto in conti
        ]

    piani_risparmio_data = []
    piani_risparmio_data = [
        {
            'id' : piano.id,
            'durata' : piano.durata,
            'obbiettivo' : float(piano.obbiettivo),
            'data_scadenza' : piano.data_scadenza.strftime('%Y-%m-%d'),  
            'data_creazione' : piano.data_creazione.strftime('%Y-%m-%d'),  
            'conto' : piano.conto.nome,
            'percentuale_completamento' : float(piano.percentuale_completamento),
            
        }
        for piano in lista_piani_risparmio
        
    ]
    
    transazioni_serializzate = []
    for transazione in lista_transazioni:
        transazioni_serializzate.append({
            'id': transazione.id,
            'descrizione': transazione.descrizione if transazione.delete != None else '',
            'importo': float(transazione.importo),  
            'data': transazione.data.strftime('%Y-%m-%d'),  # Converte la data in stringa
            'tipo_transazione': transazione.tipo_transazione,
            'conto' :  (Conto.objects.get(pk = transazione.conto.pk )).to_dict(),
            'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
            'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else 'Trasferimento',
        })
        
    obbiettivi_spesa_data = []
    for obbiettivo in lista_obbiettivi_spesa:
        obbiettivi_spesa_data.append({
            'id' : obbiettivo.id,
            'importo_speso' : float(obbiettivo.importo_speso),
            'importo' : float(obbiettivo.importo),
            'percentuale_completamento' : round(float(obbiettivo.percentuale_completamento)),
            'categoria_target' : obbiettivo.categoria_target.to_dict(),
            'tipo' : str(obbiettivo.tipo),
            'data_scadenza' : obbiettivo.data_scadenza.strftime('%Y-%m-%d'),
            'data_creazione' : obbiettivo.data_creazione.strftime('%Y-%m-%d'),
        })
   
   
    oggi = timezone.now().date()
    transazioni_odierne = lista_transazioni.filter(data=oggi)
   
    if request.method == 'POST':  
        form = NuovoConto(request.POST, request=request)
        if form.is_valid():
            conto = Conto.objects.create(
                nome=form.cleaned_data['nome'],
                tipo=form.cleaned_data['tipo'],
                saldo=form.cleaned_data['saldo'],
            )
            IntestazioniConto.objects.create(
                conto=conto,
                utente=utente,
                data_intestazione=timezone.now().date()
            )
            
            conti = AccountService.get_conti_utente(utente.pk)  # Aggiorna i conti
            conti_data = [
                {
                    'id': conto.id,
                    'nome': conto.nome,
                    'tipo': conto.tipo,
                    'saldo': conto.saldo,
                }
                for conto in conti
            ]
            
            
            
            formTransazione = NuovaTransazioneForm(utente=request.user) 
            formTransazione_html = render_to_string('personal/conto_field.html', {'formTransazione': formTransazione})
            
            formSavingPlan = NuovoPianoRisparmo(utente=request.user)
            formSavingPlan_html = render_to_string ('personal/conto_risparmio.html', {'formPiano' : formSavingPlan})
            
            AccountService.calcola_saldo_totale(utente)

            saldo_data = SaldoTotale.objects.filter(utente=utente).order_by('data_aggiornamento')
            labels = [str(saldo.data_aggiornamento) for saldo in saldo_data]  
            data = [saldo.saldo_totale for saldo in saldo_data]
            
            return JsonResponse({'success': True, 'conti': conti_data, 'formTransazione': formTransazione_html, 
                                 'formSavingPlan' : formSavingPlan_html,'labels': labels,'data': data,})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})


    context = {"conti": conti, "form": form, 'formTransazione' : formTransazione, 'formPiano' :formSavingPlan, 
               'pianiRisparmio' : lista_piani_risparmio, 'formObbiettivo' : formObbiettivoSpesa, 
               'lista_obbiettivi_spesa' : lista_obbiettivi_spesa,
               'transazioni' : lista_transazioni, 'transazioni_odierne': transazioni_odierne, 
               'conteggio_odierne' : transazioni_odierne.count(), 'labels': labels,
               'data': data, 'conti_json' : json.dumps(conti_data),
                "transazioni_serializzate": json.dumps(transazioni_serializzate),
                'piani_risparmio_json':   piani_risparmio_data,
                'obbiettivi_spesa_json' : obbiettivi_spesa_data}
    return render(request, 'personal/personalHomePage.html', context)

@login_required
def transaction_section(request):
   
    if request.method == 'POST':
     
        utente = UserService.get_utenti_by_user(request.user.pk)
        formTransazione = NuovaTransazioneForm(request.POST, utente=request.user) 
        
       
        if formTransazione.is_valid():
            conto = formTransazione.cleaned_data['conto']
            categoria = formTransazione.cleaned_data['categoria']
            obbiettivi_spesa_riguardanti = BudgetingService.get_lista_obbiettivi_spesa_by_categoria(utente,categoria)
            
            match formTransazione.cleaned_data['tipo_transazione']:
                case 'singola':
                    conto_selezionato = formTransazione.cleaned_data['conto']
                    importo = formTransazione.cleaned_data['importo']

                    # Scaliamo l'importo dal conto selezionato
                    conto = Conto.objects.get(id=conto_selezionato.id)
                    conto.saldo += importo
                    conto.save()
                    utente = UserService.get_utenti_by_user(request.user.id)
                    # Crea la nuova transazione
                    Transazione.objects.create(
                        conto=conto,
                        importo=importo,
                        data=formTransazione.cleaned_data['data'],
                        descrizione=formTransazione.cleaned_data['descrizione'],
                        tipo_transazione=formTransazione.cleaned_data['tipo_transazione'],
                        utente=  UserService.get_utenti_by_user(request.user.id),
                        categoria = formTransazione.cleaned_data['categoria'], 
                        sotto_categoria = formTransazione.cleaned_data['sotto_categoria'], 
                        eseguita = True,
                    )

                    # Aggiorna la lista dei conti
                    conti = AccountService.get_conti_utente(utente.pk)
                    conti_data = [
                        {
                            'id': conto.id,
                            'nome': conto.nome,
                            'tipo': conto.tipo,
                            'saldo': conto.saldo,
                        }
                        for conto in conti
                    ]

                    # Ottieni anche le transazioni aggiornate
                    transazioni = Transazione.objects.filter(eseguita=True).order_by('-data')
                    transazioni_data = [
                        {
                            'id': transazione.id,
                            'importo': transazione.importo,
                            'data': transazione.data,
                            'descrizione': transazione.descrizione,
                            'tipo_transazione': transazione.tipo_transazione,
                            'eseguita' : transazione.eseguita,
                            'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else None,
                            'conto' : transazione.conto.to_dict(),
                            'conto_arrivo' : transazione.conto_arrivo.to_dict() if transazione.tipo_transazione == 'trasferimento' else None,
                            'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
                        }
                        for transazione in transazioni
                    ]
                    
                    if(conto.tipo == 'risparmio'):
                        BudgetingService.ricalcola_lista_piani_risparmio(utente)
                        
                    piani = BudgetingService.get_lista_SavingPlan(utente)
                    piani_data = [
                    {
                        'id' : piano.id,
                        'obbiettivo': float(piano.obbiettivo),
                        'percentuale_completamento': float(piano.percentuale_completamento),
                        'data_scadenza' : piano.data_scadenza.strftime('%Y-%m-%d'), 
                        'data_creazione' : piano.data_creazione.strftime('%Y-%m-%d'),  
                        'conto': piano.conto.nome,
                     }
                        for piano in piani
                    ]
                    
                    if obbiettivi_spesa_riguardanti:  
                        for obbiettivo in obbiettivi_spesa_riguardanti:
                            obbiettivo.importo_speso += (-importo)
                            obbiettivo.percentuale_completamento = (obbiettivo.importo_speso/ obbiettivo.importo) * 100
                            if(obbiettivo.percentuale_completamento > 100):
                                obbiettivo.percentuale_completamento = 100
                            obbiettivo.save()
                    obbiettivi_utente = BudgetingService.get_lista_Obbiettivi_Spesa(utente)
                  
                    Obbiettivi_data = [
                        {
                            'id': obbiettivo.pk,
                            'importo': obbiettivo.importo,
                            'percentuale_completamento': obbiettivo.percentuale_completamento,
                            'categoria_target': obbiettivo.categoria_target.to_dict(),
                            'tipo': obbiettivo.tipo,
                            'data_creazione': obbiettivo.data_creazione,
                            'data_scadenza': obbiettivo.data_scadenza,
                            'importo_speso' : obbiettivo.importo_speso
                        }
                        for obbiettivo in obbiettivi_utente
                    ]
                    
                    AccountService.modifica_saldo_totale(utente, importo)


                    saldo_data = SaldoTotale.objects.filter(utente=utente).order_by('data_aggiornamento')
                    labels = [str(saldo.data_aggiornamento) for saldo in saldo_data]  # Date per l'asse X
                    data = [saldo.saldo_totale for saldo in saldo_data]
                    
                    
                    
                    return JsonResponse({
                        'success': True,
                        'conti': conti_data,
                        'transazioni': transazioni_data,
                        "piani_risparmio" : piani_data, 
                        'obbiettivi_spesa' : Obbiettivi_data,
                        'labels' : labels,
                        'data' : data,
                    })
                case 'futura':
                    if request.method == 'POST':
                        conto_selezionato = formTransazione.cleaned_data['conto']
                        importo = formTransazione.cleaned_data['importo']
                        conto = Conto.objects.get(id=conto_selezionato.id)
                        utente = UserService.get_utenti_by_user(request.user.id)
                        
                        Transazione.objects.create(
                            conto=conto,
                            importo=importo,
                            data=formTransazione.cleaned_data['data'],
                            descrizione=formTransazione.cleaned_data['descrizione'],
                            tipo_transazione=formTransazione.cleaned_data['tipo_transazione'],
                            utente=  UserService.get_utenti_by_user(request.user.id),
                            categoria = formTransazione.cleaned_data['categoria'], 
                            sotto_categoria = formTransazione.cleaned_data['sotto_categoria'], 
                            eseguita = False,
                        )

                        # Aggiorna la lista dei conti
                        conti = AccountService.get_conti_utente(utente.pk)
                        conti_data = [
                            {
                                'id': conto.id,
                                'nome': conto.nome,
                                'tipo': conto.tipo,
                                'saldo': conto.saldo,
                            }
                            for conto in conti
                        ]

                        transazioni = Transazione.objects.filter(eseguita=True).order_by('-data')
                        transazioni_data = [
                        {
                            'id': transazione.id,
                            'importo': transazione.importo,
                            'data': transazione.data,
                            'descrizione': transazione.descrizione,
                            'tipo_transazione': transazione.tipo_transazione,
                            'eseguita' : transazione.eseguita,
                            'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else None,
                            'conto' : transazione.conto.to_dict(),
                            'conto_arrivo' : transazione.conto_arrivo.to_dict() if transazione.tipo_transazione == 'trasferimento' else None,
                            'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
                        }
                        for transazione in transazioni
                        ]
                        
                        if(conto.tipo == 'risparmio'):
                            BudgetingService.ricalcola_lista_piani_risparmio(utente)
                        
                        
                        piani = BudgetingService.get_lista_SavingPlan(utente)
                        piani_data = [
                            {
                                'id' : piano.id,
                                'obbiettivo': float(piano.obbiettivo),
                                'percentuale_completamento': float(piano.percentuale_completamento),
                                'data_scadenza' : piano.data_scadenza.strftime('%Y-%m-%d'), 
                                'data_creazione' : piano.data_creazione.strftime('%Y-%m-%d'),  
                                'conto': piano.conto.nome,
                            }
                            for piano in piani
                        ]
                         
                       
                        obbiettivi_utente = BudgetingService.get_lista_Obbiettivi_Spesa(utente)
                  
                        Obbiettivi_data = [
                            {
                                'id': obbiettivo.pk,
                                'importo': obbiettivo.importo,
                                'percentuale_completamento': obbiettivo.percentuale_completamento,
                                'categoria_target': obbiettivo.categoria_target.to_dict(),
                                'tipo': obbiettivo.tipo,
                                'data_creazione': obbiettivo.data_creazione,
                                'data_scadenza': obbiettivo.data_scadenza,
                                'importo_speso' : obbiettivo.importo_speso
                            }
                            for obbiettivo in obbiettivi_utente
                        ]
                        
                        saldo_data = SaldoTotale.objects.filter(utente=utente).order_by('data_aggiornamento')
                        labels = [str(saldo.data_aggiornamento) for saldo in saldo_data]  # Date per l'asse X
                        data = [saldo.saldo_totale for saldo in saldo_data]
                        return JsonResponse({
                            'success': True,
                            'conti': conti_data,
                            'transazioni': transazioni_data,
                            "piani_risparmio" : piani_data,
                            'obbiettivi_spesa' : Obbiettivi_data,
                            'labels' : labels,
                            'data' : data,
                        })
                case 'periodica':
                    conto_selezionato = formTransazione.cleaned_data['conto']
                    conto = Conto.objects.get(id=conto_selezionato.id)
                    importo = formTransazione.cleaned_data['importo']
                    prima_data = formTransazione.cleaned_data['data']
                    utente = UserService.get_utenti_by_user(request.user.id)
                    data_prossimo_rinnovo = ''
                    data_prossimo_rinnovo_prossimo_rinnovo = ''
                    from datetime import timedelta

                    match formTransazione.cleaned_data['tipo_rinnovo']:
                        case 'settimanale': 
                            data_prossimo_rinnovo = prima_data + timedelta(days=7)
                            data_prossimo_rinnovo_prossimo_rinnovo = data_prossimo_rinnovo + timedelta(days=7)
                        case 'mensile': 
                            data_prossimo_rinnovo = prima_data + timedelta(days=30)
                            data_prossimo_rinnovo_prossimo_rinnovo = data_prossimo_rinnovo + timedelta(days=30)
                        case 'semestrale':
                            data_prossimo_rinnovo = prima_data + timedelta(days=180)
                            data_prossimo_rinnovo_prossimo_rinnovo = data_prossimo_rinnovo + timedelta(days=180)

                                
                    if(prima_data <= timezone.now().date()):
                        
                        conto.saldo += importo
                        conto.save()
                        Transazione.objects.create(
                        conto=conto,
                        importo=importo,
                        data=formTransazione.cleaned_data['data'],
                        descrizione=formTransazione.cleaned_data['descrizione'],
                        tipo_transazione=formTransazione.cleaned_data['tipo_transazione'],
                        utente=  UserService.get_utenti_by_user(request.user.id),
                        categoria = formTransazione.cleaned_data['categoria'], 
                        sotto_categoria = formTransazione.cleaned_data['sotto_categoria'], 
                        eseguita = True,
                        prossimo_rinnovo = data_prossimo_rinnovo,
                        tipo_rinnovo = formTransazione.cleaned_data['tipo_rinnovo'], 
                        )
                        
                        
                        Transazione.objects.create(
                        conto=conto,
                        importo=importo,
                        data= data_prossimo_rinnovo,
                        descrizione=formTransazione.cleaned_data['descrizione'],
                        tipo_transazione=formTransazione.cleaned_data['tipo_transazione'],
                        utente=  UserService.get_utenti_by_user(request.user.id),
                        categoria = formTransazione.cleaned_data['categoria'], 
                        sotto_categoria = formTransazione.cleaned_data['sotto_categoria'], 
                        eseguita = False,
                        prossimo_rinnovo = data_prossimo_rinnovo_prossimo_rinnovo, 
                        tipo_rinnovo = formTransazione.cleaned_data['tipo_rinnovo'], 
                        )
                        AccountService.modifica_saldo_totale(utente, importo)
                        if obbiettivi_spesa_riguardanti:  
                         for obbiettivo in obbiettivi_spesa_riguardanti:
                            obbiettivo.importo_speso += (-importo)
                            obbiettivo.percentuale_completamento = (obbiettivo.importo_speso/ obbiettivo.importo) * 100
                            if(obbiettivo.percentuale_completamento > 100):
                                obbiettivo.percentuale_completamento = 100
                            obbiettivo.save()
                    else:
                        Transazione.objects.create(
                        conto=conto,
                        importo=importo,
                        data=formTransazione.cleaned_data['data'],
                        descrizione=formTransazione.cleaned_data['descrizione'],
                        tipo_transazione=formTransazione.cleaned_data['tipo_transazione'],
                        utente=  UserService.get_utenti_by_user(request.user.id),
                        categoria = formTransazione.cleaned_data['categoria'], 
                        sotto_categoria = formTransazione.cleaned_data['sotto_categoria'], 
                        eseguita = False,
                        prossimo_rinnovo = data_prossimo_rinnovo,
                        tipo_rinnovo = formTransazione.cleaned_data['tipo_rinnovo'], 
                        )
                        
                    conti = AccountService.get_conti_utente(utente.pk)
                    conti_data = [
                        {
                            'id': conto.id,
                            'nome': conto.nome,
                            'tipo': conto.tipo,
                            'saldo': conto.saldo,
                        }
                        for conto in conti
                    ]
                    

                    transazioni = Transazione.objects.filter(eseguita=True).order_by('-data')
                    transazioni_data = [
                        {
                            'id': transazione.id,
                            'importo': transazione.importo,
                            'data': transazione.data,
                            'descrizione': transazione.descrizione,
                            'tipo_transazione': transazione.tipo_transazione,
                            'eseguita' : transazione.eseguita,
                            'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else None,
                            'conto' : transazione.conto.to_dict(),
                            'conto_arrivo' : transazione.conto_arrivo.to_dict() if transazione.tipo_transazione == 'trasferimento' else None,
                            'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
                        }
                        for transazione in transazioni
                    ]
                    
                    if(conto.tipo == 'risparmio'):
                        BudgetingService.ricalcola_lista_piani_risparmio(utente)
                        
                    
                    piani = BudgetingService.get_lista_SavingPlan(utente)
                    piani_data = [
                        {
                            'id' : piano.id,
                            'obbiettivo': float(piano.obbiettivo),
                            'percentuale_completamento': float(piano.percentuale_completamento),
                            'data_scadenza' : piano.data_scadenza.strftime('%Y-%m-%d'), 
                            'data_creazione' : piano.data_creazione.strftime('%Y-%m-%d'),  
                            'conto': piano.conto.nome,
                        }
                        for piano in piani
                    ]
                            
                    obbiettivi_utente = BudgetingService.get_lista_Obbiettivi_Spesa(utente)
                  
                    Obbiettivi_data = [
                            {
                                'id': obbiettivo.pk,
                                'importo': obbiettivo.importo,
                                'percentuale_completamento': obbiettivo.percentuale_completamento,
                                'categoria_target': obbiettivo.categoria_target.to_dict(),
                                'tipo': obbiettivo.tipo,
                                'data_creazione': obbiettivo.data_creazione,
                                'data_scadenza': obbiettivo.data_scadenza,
                                'importo_speso' : obbiettivo.importo_speso
                            }
                            for obbiettivo in obbiettivi_utente
                        ]
                    
                    saldo_data = SaldoTotale.objects.filter(utente=utente).order_by('data_aggiornamento')
                    labels = [str(saldo.data_aggiornamento) for saldo in saldo_data]  # Date per l'asse X
                    data = [saldo.saldo_totale for saldo in saldo_data]
                        
                    return JsonResponse({
                        'success': True,
                        'conti': conti_data,
                        'transazioni': transazioni_data,
                        "piani_risparmio" : piani_data,
                        'obbiettivi_spesa' : Obbiettivi_data,
                        'labels' : labels,
                        'data' : data,
                    })
                case 'trasferimento':
                    conto_partenza = formTransazione.cleaned_data['conto']
                    conto_destinazione = formTransazione.cleaned_data['conto_arrivo']
                    importo = formTransazione.cleaned_data['importo']

                # A -> B
                    conto = Conto.objects.get(id=conto_partenza.id)
                    conto.saldo -= importo
                    conto.save()
                    utente = UserService.get_utenti_by_user(request.user.id)
                    # Crea la nuova transazione
                    Transazione.objects.create(
                        conto=conto,
                        importo=importo,
                        data=formTransazione.cleaned_data['data'],
                        descrizione=formTransazione.cleaned_data['descrizione'],
                        tipo_transazione=formTransazione.cleaned_data['tipo_transazione'],
                        utente=  UserService.get_utenti_by_user(request.user.id),
                        categoria = formTransazione.cleaned_data['categoria'], 
                        sotto_categoria = formTransazione.cleaned_data['sotto_categoria'], 
                        eseguita = True,
                        conto_arrivo = conto_destinazione
                        
                    )
                
                 # B -> A
                    conto = Conto.objects.get(id=conto_destinazione.id)
                    conto.saldo += importo
                    conto.save()
                   

                    
                    conti = AccountService.get_conti_utente(utente.pk)
                    conti_data = [
                        {
                            'id': conto.id,
                            'nome': conto.nome,
                            'tipo': conto.tipo,
                            'saldo': conto.saldo,
                        }
                        for conto in conti
                    ]
                    transazioni = Transazione.objects.filter(eseguita=True).order_by('-data')
                    transazioni_data = [
                        {
                            'id': transazione.id,
                            'importo': transazione.importo,
                            'data': transazione.data,
                            'descrizione': transazione.descrizione,
                            'tipo_transazione': transazione.tipo_transazione,
                            'eseguita' : transazione.eseguita,
                            'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else None,
                            'conto' : transazione.conto.to_dict(),
                            'conto_arrivo' : transazione.conto_arrivo.to_dict() if transazione.tipo_transazione == 'trasferimento' else None,
                            'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
                        }
                        for transazione in transazioni
                    ]

                    if(conto.tipo == 'risparmio'):
                        BudgetingService.ricalcola_lista_piani_risparmio(utente)
                        
                    
                    
                    piani = BudgetingService.get_lista_SavingPlan(utente)
                    piani_data = [
                        {
                            'id' : piano.id,
                            'obbiettivo': float(piano.obbiettivo),
                            'percentuale_completamento': float(piano.percentuale_completamento),
                            'data_scadenza' : piano.data_scadenza.strftime('%Y-%m-%d'), 
                            'data_creazione' : piano.data_creazione.strftime('%Y-%m-%d'),  
                            'conto': piano.conto.nome,
                        }
                        for piano in piani
                    ]

                    obbiettivi_utente = BudgetingService.get_lista_Obbiettivi_Spesa(utente)
                  
                    Obbiettivi_data = [
                        {
                            'id': obbiettivo.pk,
                            'importo': obbiettivo.importo,
                            'percentuale_completamento': obbiettivo.percentuale_completamento,
                            'categoria_target': obbiettivo.categoria_target.to_dict(),
                            'tipo': obbiettivo.tipo,
                            'data_creazione': obbiettivo.data_creazione,
                            'data_scadenza': obbiettivo.data_scadenza,
                            'importo_speso' : obbiettivo.importo_speso
                        }
                        for obbiettivo in obbiettivi_utente
                    ]
                    
                    saldo_data = SaldoTotale.objects.filter(utente=utente).order_by('data_aggiornamento')
                    labels = [str(saldo.data_aggiornamento) for saldo in saldo_data]  # Date per l'asse X
                    data = [saldo.saldo_totale for saldo in saldo_data]

                    return JsonResponse({
                        'success': True,
                        'conti': conti_data,
                        'transazioni': transazioni_data,
                        "piani_risparmio" : piani_data,
                        'obbiettivi_spesa' : Obbiettivi_data,
                        'labels' : labels,
                        'data' : data,
                    })
        else:
            return JsonResponse({'success': False, 'errors': formTransazione.errors}, status=400)

   
    
    utente = UserService.get_utenti_by_user(request.user.id)
    conti = AccountService.get_conti_utente(utente.pk)

    formTransazione = NuovaTransazioneForm(utente=request.user)  # Passa direttamente l'utente
    context = {"conti": conti, "formTransazione": formTransazione}
    return render(request, 'personal/transactionPage.html', context)

@login_required
def savings_section(request):
    
    utente = UserService.get_utenti_by_user(request.user.pk)
    conti = AccountService.get_conti_utente(utente.pk)
    formSavingPlan = NuovoPianoRisparmo(utente=request.user)
    
    if request.method == 'POST':  
        formSavingPlan = NuovoPianoRisparmo(request.POST, utente = request.user)
        if formSavingPlan.is_valid():
            conto = formSavingPlan.cleaned_data['conto']
            obbiettivo = formSavingPlan.cleaned_data['obbiettivo']
            data_scadenza = formSavingPlan.cleaned_data['data_scadenza']
            
            
            PianoDiRisparmio.objects.create(
                durata = (data_scadenza - (timezone.now().date())).days,
                obbiettivo = obbiettivo ,
                data_scadenza = data_scadenza ,
                data_creazione = timezone.now().date(),
                conto = conto,
                percentuale_completamento = (conto.saldo / obbiettivo) * 100,
    
            )
            
            
            piani = BudgetingService.get_lista_SavingPlan(utente)
            piani_data = [
                {
                    'id' : piano.id,
                    'obbiettivo': float(piano.obbiettivo),
                    'percentuale_completamento': float(piano.percentuale_completamento),
                    'data_scadenza' : piano.data_scadenza.strftime('%Y-%m-%d'), 
                    'data_creazione' : piano.data_creazione.strftime('%Y-%m-%d'),  
                    'conto': piano.conto.nome,
                }
                for piano in piani
            ]
            
        
       
        
    
            
            return JsonResponse({'success': True, "piani_risparmio" : piani_data })
        else:
            return JsonResponse({'success': False, 'errors': formSavingPlan.errors})

    context = {"conti": conti, "formPiano": formSavingPlan}
    return render(request, 'personal/personalHomePage.html', context)

@login_required
def elimina_transazione(request, id):
    if request.method == 'POST':
        transazione = Transazione.objects.get(pk = id)
        conto = Conto.objects.get(pk = transazione.conto.pk)
        conto.saldo -= transazione.importo
        conto.save()
        transazione.delete()  
        utente = UserService.get_utenti_by_user(request.user.pk)
    
        lista_transazioni = BudgetingService.get_transazioni_by_utente(utente).filter(eseguita=True).order_by('-data')
        transazioni_serializzate = []
        for transazione in lista_transazioni:
            transazioni_serializzate.append({
                'id': transazione.id,
                'descrizione': transazione.descrizione if transazione.delete != None else '',
                'importo': float(transazione.importo),  
                'data': transazione.data.strftime('%Y-%m-%d'),  # Converte la data in stringa
                'tipo_transazione': transazione.tipo_transazione,
                'conto_id' :  float(Conto.objects.get(pk = transazione.conto.pk ).pk),
                'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
                'categoria' : transazione.categoria.nome if transazione.categoria != None else 'Trasferimento',
            })
            
       
        return JsonResponse(transazioni_serializzate, safe=False)



@login_required
def obbiettivoSpesa_section(request):
        utente = UserService.get_utenti_by_user(request.user.pk)
        
        if request.method == 'POST':  
            formSpendingGoal = ObbiettivoSpesaForm(request.POST)
            if formSpendingGoal.is_valid():
                tipo = formSpendingGoal.cleaned_data['tipo']

                # Calcola la data di scadenza in base al tipo
                data_creazione = timezone.now().date()

                if tipo == 'mensile':
                    data_scadenza = data_creazione + timedelta(days=30)  # Approximation for one month
                elif tipo == 'trimestrale':
                    data_scadenza = data_creazione + timedelta(days=90)  # Approximation for three months
                elif tipo == 'semestrale':
                    data_scadenza = data_creazione + timedelta(days=180)  # Approximation for six months
                elif tipo == 'annuale':
                    data_scadenza = data_creazione + timedelta(days=365)  # One year
                else:
                    data_scadenza = data_creazione # fallback in caso di errore

                # Crea l'oggetto ObbiettivoSpesa usando i dati del form
                ObbiettivoSpesa.objects.create(
                    importo=formSpendingGoal.cleaned_data['importo'],
                    percentuale_completamento=0,
                    utente=utente,
                    categoria_target=formSpendingGoal.cleaned_data['categoria_target'],
                    tipo=tipo,
                    data_creazione=data_creazione,
                    data_scadenza=data_scadenza, 
                    importo_speso = 0
                )

                # Ottieni la lista degli obiettivi dell'utente
                obbiettivi_utente = BudgetingService.get_lista_Obbiettivi_Spesa(utente)
                    
                Obbiettivi_data = [
                    {
                        'id': obbiettivo.pk,
                        'importo': obbiettivo.importo,
                        'percentuale_completamento': obbiettivo.percentuale_completamento,
                        'categoria_target': obbiettivo.categoria_target.to_dict(),
                        'tipo': obbiettivo.tipo,
                        'data_creazione': obbiettivo.data_creazione,
                        'data_scadenza': obbiettivo.data_scadenza,
                        'importo_speso' : obbiettivo.importo_speso
                    }
                    for obbiettivo in obbiettivi_utente
                ]
                
                return JsonResponse({'success': True, 'obbiettivi_spesa': Obbiettivi_data})
            else:
                
                return JsonResponse({'success': False, 'errors': formSpendingGoal.errors})

        
        return render(request, 'personal/personalHomePage.html')



@login_required
def elimina_conto(request, id):
    if request.method == 'POST':
        try:
            conto = Conto.objects.get(pk=id)
            conto.delete()
            
            persone_intestate = IntestazioniConto.objects.filter(conto=id)
            persone_intestate.delete()  # Usa il metodo delete() su un queryset, più efficiente
            
            response_data = {
                'success': True,
                'message': 'Conto eliminato con successo.'
            }
        except Conto.DoesNotExist:
            response_data = {
                'success': False,
                'message': 'Il conto non esiste.'
            }
        
        return JsonResponse(response_data)
    else:
        return JsonResponse({'success': False, 'message': 'Metodo non permesso.'}, status=405)



@login_required
def rename_conto(request, id, new_name):
    if request.method == 'POST':
        try:
            utente = UserService.get_utenti_by_user(request.user.id)
            
            conti_utente = AccountService.get_conti_utente(utente)
            
            if any(conto.nome == new_name for conto in conti_utente):
                return JsonResponse({
                    'success': False,
                    'message': "Hai già un conto con questo nome",
                })
                
            conto = Conto.objects.get(pk=id)
            conto.nome = new_name
            conto.save()
            
            response_data = {
                'success': True,
            }
            
        except Conto.DoesNotExist:
            response_data = {
                'success': False,
            }
        
        return JsonResponse(response_data)
    else:
        return JsonResponse({'success': False}, status=405)



@login_required
def cambia_obbiettivo_view(request, id, new_obbiettivo):
    if request.method == 'POST':
        try:
            
            utente = UserService.get_utenti_by_user(request.user.id)
            
            
           
            
            piano = (BudgetingService.get_lista_SavingPlan(utente)).get(pk = id)
         
        
            # Modifica l'obbiettivo
            piano.obbiettivo = Decimal(new_obbiettivo)
            piano.save()
        
            percentuale = BudgetingService.ricacola_percentuale_completamento(request,id)

            percentuale_troncata = round(percentuale, 2)
            
            response_data = {
                'success': True,
                'percentuale': percentuale_troncata,
            }
        except ObjectDoesNotExist:  # Cattura l'eccezione corretta
            response_data = {
                'success': False,
                'error': 'Piano di risparmio non trovato'
            }
        except Exception as e:
            response_data = {
                'success': False,
                'error': str(e)
            }

        return JsonResponse(response_data)
    else:
        return JsonResponse({'success': False}, status=405)


@login_required
def cambia_data_scadenza_view(request, id, new_date):
    if request.method == 'POST':
        try:
            utente = UserService.get_utenti_by_user(request.user.id)
            
            piano = (BudgetingService.get_lista_SavingPlan(utente)).get(pk = id)
            
            piano.data_scadenza = new_date
            
            piano.save()
            
            
            response_data = {
                'success': True,
            }
            
        except piano.DoesNotExist:
            response_data = {
                'success': False,
            }
        
        return JsonResponse(response_data)
    else:
        return JsonResponse({'success': False}, status=405)





@login_required
def elimina_piano_view(request, id):
    if request.method == 'POST':
        try:
            piano = PianoDiRisparmio.objects.get(pk=id)
            piano.delete()
            
            response_data = {
                'success': True,
                'message': 'Piano eliminato con successo.'
            }
        except Conto.DoesNotExist:
            response_data = {
                'success': False,
                'message': 'Il piano non esiste.'
            }
        
        return JsonResponse(response_data)
    else:
        return JsonResponse({'success': False, 'message': 'Metodo non permesso.'}, status=405)

@login_required
def cambia_obbiettivo_obbiettivoSpesa_view(request, id, new_obbiettivo):
    if request.method == 'POST':
        try:   
            utente = UserService.get_utenti_by_user(request.user.id)
            print(utente)
            obbiettivo = (BudgetingService.get_lista_Obbiettivi_Spesa(utente)).get(pk = id)
            print(obbiettivo)
            obbiettivo.importo = Decimal(new_obbiettivo)
            obbiettivo.save()
        
            
            percentuale = BudgetingService.ricalcola_percentuale_completamento_obbiettivoSpesa(request,id)
            print(percentuale)
            percentuale_troncata = round(percentuale, 2)
            
            response_data = {
                'success': True,
                'percentuale': percentuale_troncata,
            }
        except ObjectDoesNotExist:  # Cattura l'eccezione corretta
            response_data = {
                'success': False,
                'error': 'Obbiettivo non trovato'
            }
        except Exception as e:
            response_data = {
                'success': False,
                'error': str(e)
            }

        return JsonResponse(response_data)
    else:
        return JsonResponse({'success': False}, status=405)

@login_required
def cambia_data_scadenza_obbiettivoSpesa_view(request, id, new_date):
    if request.method == 'POST':
        try:
            utente = UserService.get_utenti_by_user(request.user.id)
            
            obbiettivo = (BudgetingService.get_lista_Obbiettivi_Spesa(utente)).get(pk = id)
            
            obbiettivo.data_scadenza = new_date
            
            obbiettivo.save()
            
            
            response_data = {
                'success': True,
            }
            
        except obbiettivo.DoesNotExist:
            response_data = {
                'success': False,
            }
        
        return JsonResponse(response_data)
    else:
        return JsonResponse({'success': False}, status=405)


@login_required
def elimina_obbiettivo_view(request, id):
    if request.method == 'POST':
        try:
            obbiettivo = ObbiettivoSpesa.objects.get(pk=id)
            obbiettivo.delete()
            
            response_data = {
                'success': True,
                'message': 'Obbiettivo eliminato con successo.'
            }
        except Conto.DoesNotExist:
            response_data = {
                'success': False,
                'message': 'L obbiettivo non esiste.'
            }
        
        return JsonResponse(response_data)
    else:
        return JsonResponse({'success': False, 'message': 'Metodo non permesso.'}, status=405)
