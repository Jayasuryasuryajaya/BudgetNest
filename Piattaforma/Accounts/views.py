from django.shortcuts import render
from .services import *
from django.contrib.auth.decorators import login_required
from .services import AccountService
from Users.services import *
from .forms import *
from django.http import JsonResponse
from django.utils import timezone  # Assicurati di importare timezone
from datetime import date
from Budgeting.forms import *
from django.template.loader import render_to_string
from Budgeting.services import *
from datetime import timedelta


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
            
            return JsonResponse({'success': True, 'conti': conti_data, 'formTransazione': formTransazione_html, 
                                 'formSavingPlan' : formSavingPlan_html,'labels': labels,'data': data,})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})


    context = {"conti": conti, "form": form, 'formTransazione' : formTransazione, 'formPiano' :formSavingPlan, 
               'pianiRisparmio' : lista_piani_risparmio, 'formObbiettivo' : formObbiettivoSpesa, 
               'lista_obbiettivi_spesa' : lista_obbiettivi_spesa,
               'transazioni' : lista_transazioni, 'transazioni_odierne': transazioni_odierne, 
               'conteggio_odierne' : transazioni_odierne.count(), 'labels': labels,'data': data,}
    return render(request, 'personal/personalHomePage.html', context)

@login_required
def transaction_section(request):
   
    if request.method == 'POST':
        print("Ricevuta una richiesta POST.")
        utente = UserService.get_utenti_by_user(request.user.pk)
        formTransazione = NuovaTransazioneForm(request.POST, utente=request.user) 
        
        print(formTransazione)
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
                        }
                        for transazione in transazioni
                    ]
                    
                    if(conto.tipo == 'risparmio'):
                        BudgetingService.ricalcola_lista_piani_risparmio(utente)
                        
                    piani = BudgetingService.get_lista_SavingPlan(utente)
                    piani_data = [
                        {
                            'id' : piano.pk,
                            'obbiettivo': piano.obbiettivo,
                            'percentuale_completamento': piano.percentuale_completamento,
                            'data_scadenza': piano.data_scadenza,
                            'conto': piano.conto.to_dict(),
                        }
                        for piano in piani
                    ]
                    
                    if obbiettivi_spesa_riguardanti:  
                        for obbiettivo in obbiettivi_spesa_riguardanti:
                            obbiettivo.importo_speso += (-importo)
                            obbiettivo.percentuale_completamento = (obbiettivo.importo_speso/ obbiettivo.importo) * 100
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
                        }
                        for transazione in transazioni
                        ]
                        
                        if(conto.tipo == 'risparmio'):
                            BudgetingService.ricalcola_lista_piani_risparmio(utente)
                        
                        piani = BudgetingService.get_lista_SavingPlan(utente)
                        piani_data = [
                        {
                                'id' : piano.pk,
                                'obbiettivo': piano.obbiettivo,
                                'percentuale_completamento': piano.percentuale_completamento,
                                'data_scadenza': piano.data_scadenza,
                                'conto': piano.conto.to_dict(),
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
                        }
                        for transazione in transazioni
                    ]
                    
                    if(conto.tipo == 'risparmio'):
                        BudgetingService.ricalcola_lista_piani_risparmio(utente)
                        
                    piani = BudgetingService.get_lista_SavingPlan(utente)
                    piani_data = [
                        {
                            'id' : piano.pk,
                            'obbiettivo': piano.obbiettivo,
                            'percentuale_completamento': piano.percentuale_completamento,
                            'data_scadenza': piano.data_scadenza,
                            'conto': piano.conto.to_dict(),
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
                        }
                        for transazione in transazioni
                    ]

                    if(conto.tipo == 'risparmio'):
                        BudgetingService.ricalcola_lista_piani_risparmio(utente)
                        
                    piani = BudgetingService.get_lista_SavingPlan(utente)
                    piani_data = [
                        {
                            'id' : piano.pk,
                            'obbiettivo': piano.obbiettivo,
                            'percentuale_completamento': piano.percentuale_completamento,
                            'data_scadenza': piano.data_scadenza,
                            'conto': piano.conto.to_dict(),
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

   
    print("Ricevuta una richiesta GET.")
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
                    'id' : piano.pk,
                    'obbiettivo': piano.obbiettivo,
                    'percentuale_completamento': piano.percentuale_completamento,
                    'data_scadenza': piano.data_scadenza,
                    'conto': piano.conto.to_dict(),
                }
                for piano in piani
            ]
            
           
            
            return JsonResponse({'success': True, "piani_risparmio" : piani_data })
        else:
            return JsonResponse({'success': False, 'errors': formSavingPlan.errors})

    context = {"conti": conti, "formPiano": formSavingPlan}
    return render(request, 'personal/personalHomePage.html', context)




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
