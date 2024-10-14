import os
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
from django.shortcuts import redirect
from Challenges.forms import *
import urllib.request
from Challenges.services import * 
from Budgeting.models import * 

@login_required
def dashboard_utente(request):
    utente = UserService.get_utenti_by_user(request.user.pk)
    AccountService.calcola_saldo_totale(utente)
    AccountService.calcola_saldo_totale_investimenti(utente)
    ChallengeService.concludi_sfida(utente)
    return render(request, 'dashboard/dashboard.html')

@login_required
def dashboard_family(request):
    utente = UserService.get_utenti_by_user(request.user.pk)
    context = {'numero_famiglie': utente.famiglia.count()}
    return render(request, 'family/dashboard_family.html', context)


@login_required
def family_switch(request):
    utente = UserService.get_utenti_by_user(request.user.pk)
    numero_famiglie = utente.famiglia.count()
    if numero_famiglie == 1:
        famiglia = utente.famiglia.first()
        return accedi_famiglia(request, famiglia.id)
    context = {'famiglie': utente.famiglia.all()} 
    return render(request, 'family/family_choice.html', context)


@login_required
def accedi_famiglia(request, id):
    utente = UserService.get_utenti_by_user(request.user.pk)
    famiglia = utente.famiglia.filter(pk = id) 
    conti = AccountService.get_family_accounts(famiglia.first())
    formConto = NuovoContoFamiglia()
    formSfida = NuovaSfidaFamigliare(utente= utente, famiglia= famiglia.first())
    formSavingPlan = NuovoPianoRisparmoFamiglia(famiglia=famiglia.first())
    formTransazione = NuovaTransazioneFamigliaForm(utente=request.user, famiglia= famiglia.first())
    lista_piani_risparmio = BudgetingService.get_lista_SavingPlan_by_conto(conti)
    challenge_list = ChallengeService.get_family_challenge(famiglia.first())
    today = timezone.now().date()
    lista_transazioni = []
    for conto in conti:
        lista_transazioni.append(Transazione.objects.filter(eseguita=True).filter(conto = conto).order_by('-data'))
    
    transazioni_serializzate = []
    for blocco_transazione in lista_transazioni:
        for transazione in blocco_transazione:
            conto = (Conto.objects.get(pk = transazione.conto.pk )).to_dict()
            if(conto['tipo'] == TipoConto.RISPARMIO):
                transazioni_serializzate.append({
                    'id': transazione.id,
                    'descrizione': transazione.descrizione if transazione.delete != None else '',
                    'importo': float(transazione.importo),  
                    'data': transazione.data.strftime('%Y-%m-%d'),  # Converte la data in stringa
                    'tipo_transazione': transazione.tipo_transazione,
                    'conto' :  (Conto.objects.get(pk = transazione.conto.pk )).to_dict(),
                    'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
                    'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else 'Trasferimento',
                    'sottocategoria' : transazione.sotto_categoria.to_dict() if transazione.sotto_categoria != None else None,
                    'utente' : (transazione.utente).to_dict(),
                })
    conti_data = []
    conti_data = [
                {
                    'id': conto.id,
                    'nome': conto.nome,
                    'tipo': conto.tipo,
                    'saldo': float(conto.saldo),
                }
                for conto in conti
        ]
    challenge_json = []
    challenge_json = [
                            {
                                'id' : sfida_item.pk,
                                'importo_sfidante' : sfida_item.importo_sfidante,
                                'importo_sfidato' : sfida_item.importo_sfidato,
                                'percentuale_sfidante' : sfida_item.percentuale_sfidante,
                                'percentuale_sfidato' : sfida_item.percentuale_sfidato,
                                'categoria_target' : sfida_item.categoria_target.to_dict(),
                                'sfidante' : sfida_item.sfidante.to_dict(),
                                'sfidato' : sfida_item.sfidato.to_dict(),
                                'descrizione' : sfida_item.descrizione,
                                'data_scadenza' : sfida_item.data_scadenza.strftime('%Y-%m-%d'),
                                'data_creazione' : sfida_item.data_creazione.strftime('%Y-%m-%d'),  
                                'conclusa' : "true" if sfida_item.conclusa else "false",
                            }
                            for sfida_item in challenge_list
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
    
   
    context = {'famiglia': famiglia.first(),
               'conti' : conti,
               'formConto' : formConto,
               "transazioni_serializzate": json.dumps(transazioni_serializzate),
               'conti_json' : json.dumps(conti_data),
               'pianiRisparmio' : lista_piani_risparmio,
               'piani_risparmio_json':   piani_risparmio_data,
               'formPiano' :formSavingPlan,
               'utente' : utente,
               'formTransazione' : formTransazione, 
               'formSfida' : formSfida,
               'challenge' : challenge_list,
               'challenge_json' : challenge_json,
               'today' : today,
               }
    return render(request, 'family/family.html', context)
 
@login_required
def crea_account_famiglia(request, id):
    utente = UserService.get_utenti_by_user(request.user.pk)
    famiglia = Famiglia.objects.get(pk = id)
    if request.method == 'POST':  
        form = NuovoContoFamiglia(request.POST, request=request)
        if form.is_valid():
            conto = Conto.objects.create(
                nome=form.cleaned_data['nome'],
                tipo= TipoConto.RISPARMIO,
                saldo=form.cleaned_data['saldo'],
                condiviso = True,
            )
            persone = AccountService.get_family_members(famiglia) 
            for persona in persone:  
                IntestazioniConto.objects.create(
                    conto=conto,
                    utente=persona,
                    data_intestazione=timezone.now().date()
                )
                AccountService.calcola_saldo_totale(utente)
            
            conti = AccountService.get_family_accounts(famiglia)
            conti_data = [
                {
                    'id': conto.id,
                    'nome': conto.nome,
                    'tipo': conto.tipo,
                    'saldo': conto.saldo,
                    'condiviso' : conto.condiviso
                }
                for conto in conti
            ]
            
            return JsonResponse({'success': True, 'conti': conti_data})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})


@login_required
def personal_section(request):
    BudgetingService.check_future_transactions(request)
    utente = UserService.get_utenti_by_user(request.user.pk)
    AccountService.calcola_saldo_totale(utente)
    AccountService.calcola_saldo_totale_investimenti(utente)
    form = NuovoConto()
    formTransazione = NuovaTransazioneForm(utente=request.user)
    conti = AccountService.get_conti_utente(utente.pk)
    formSavingPlan = NuovoPianoRisparmo(utente=request.user)
    formObbiettivoSpesa = ObbiettivoSpesaForm()
    lista_piani_risparmio = BudgetingService.get_lista_SavingPlan(utente)
    lista_obbiettivi_spesa = BudgetingService.get_lista_Obbiettivi_Spesa(utente)
    lista_transazioni = BudgetingService.get_transazioni_by_conti(conti).order_by('-data')
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
            'sottocategoria' : transazione.sotto_categoria.to_dict() if transazione.sotto_categoria != None else None,
            'utente' : (transazione.utente).to_dict(),
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
            formSavingPlanContoArrivo_html = render_to_string ('personal/conto_field_arrivo.html', {'formTransazione' : formTransazione})
            
            formSavingPlan = NuovoPianoRisparmo(utente=request.user)
            formSavingPlan_html = render_to_string ('personal/conto_risparmio.html', {'formPiano' : formSavingPlan})
            
            
            AccountService.calcola_saldo_totale(utente)

            saldo_data = SaldoTotale.objects.filter(utente=utente).order_by('data_aggiornamento')
            labels = [str(saldo.data_aggiornamento) for saldo in saldo_data]  
            data = [saldo.saldo_totale for saldo in saldo_data]
            
            return JsonResponse({'success': True, 'conti': conti_data, 'formTransazione': formTransazione_html, 
                                 'formSavingPlan' : formSavingPlan_html,'labels': labels,'data': data, 'formContoArrivo': formSavingPlanContoArrivo_html})
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
                'obbiettivi_spesa_json' : obbiettivi_spesa_data, 'utente' : utente
                }
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
                    data = formTransazione.cleaned_data['data']
                    # Scaliamo l'importo dal conto selezionato
                    conto = Conto.objects.get(id=conto_selezionato.id)
                    conto.saldo += importo
                    conto.save()
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
                        eseguita = True,
                    )

                    ChallengeService.aggiorna_sfida(utente,formTransazione.cleaned_data['categoria'],importo)
                    
                    
                    
                   
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

                    transazioni = BudgetingService.get_transazioni_by_conti(conti).order_by('-data')
                    
                    transazioni_data = [
                        {
                            'id': transazione.id,
                            'importo': transazione.importo,
                            'data': transazione.data,
                            'descrizione': transazione.descrizione,
                            'tipo_transazione': transazione.tipo_transazione,
                            'eseguita' : transazione.eseguita,
                            'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else None,
                            'sottocategoria' : transazione.sotto_categoria.to_dict() if transazione.sotto_categoria != None else None,
                            'conto' : transazione.conto.to_dict(),
                            'conto_arrivo' : transazione.conto_arrivo.to_dict() if transazione.tipo_transazione == 'trasferimento' else None,
                            'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
                             'utente' : (transazione.utente).to_dict(),
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
                    
                    BudgetingService.aggiorna_saldo_totale_dopo_inserimento(utente, data, importo)
                    
                    if obbiettivi_spesa_riguardanti:  
                        for obbiettivo in obbiettivi_spesa_riguardanti:
                             if obbiettivo.data_creazione <= data <= obbiettivo.data_scadenza:
                                obbiettivo.importo_speso += (-importo)
                                obbiettivo.percentuale_completamento = (obbiettivo.importo_speso/ obbiettivo.importo) * 100
                                if(obbiettivo.percentuale_completamento > 100):
                                    obbiettivo.percentuale_completamento = 100
                                if(obbiettivo.percentuale_completamento <= 0):
                                    obbiettivo.percentuale_completamento = 0
                                obbiettivo.save()
                            
                    
                        
                    obbiettivi_utente = BudgetingService.get_lista_Obbiettivi_Spesa(utente)
                  
                    Obbiettivi_data = [
                        {
                            'id': obbiettivo.pk,
                            'importo': obbiettivo.importo,
                            'percentuale_completamento': round(obbiettivo.percentuale_completamento),
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
                        transazioni = BudgetingService.get_transazioni_by_conti(conti).order_by('-data')
                        transazioni = Transazione.objects.filter(eseguita=True).filter(utente = utente).order_by('-data')
                        transazioni_data = [
                        {
                            'id': transazione.id,
                            'importo': transazione.importo,
                            'data': transazione.data,
                            'descrizione': transazione.descrizione,
                            'tipo_transazione': transazione.tipo_transazione,
                            'eseguita' : transazione.eseguita,
                            'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else None,
                            'sottocategoria' : transazione.sotto_categoria.to_dict() if transazione.sotto_categoria != None else None,
                            'conto' : transazione.conto.to_dict(),
                            'conto_arrivo' : transazione.conto_arrivo.to_dict() if transazione.tipo_transazione == 'trasferimento' else None,
                            'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
                            'utente' : (transazione.utente).to_dict(),
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
                                'percentuale_completamento': round(obbiettivo.percentuale_completamento),
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
                        data = formTransazione.cleaned_data['data'],
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
                        ChallengeService.aggiorna_sfida(utente,formTransazione.cleaned_data['categoria'],importo)
                        BudgetingService.aggiorna_saldo_totale_dopo_inserimento(utente, data, importo)
                    
        
                        
                        if obbiettivi_spesa_riguardanti:  
                         for obbiettivo in obbiettivi_spesa_riguardanti:
                              if obbiettivo.data_creazione <= data <= obbiettivo.data_scadenza:
                                obbiettivo.importo_speso += (-importo)
                                obbiettivo.percentuale_completamento = (obbiettivo.importo_speso/ obbiettivo.importo) * 100
                                if(obbiettivo.percentuale_completamento > 100):
                                    obbiettivo.percentuale_completamento = 100
                                if(obbiettivo.percentuale_completamento <= 0):
                                    obbiettivo.percentuale_completamento = 0
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
                    
                    transazioni = BudgetingService.get_transazioni_by_conti(conti).order_by('-data')
                    transazioni_data = [
                        {
                            'id': transazione.id,
                            'importo': transazione.importo,
                            'data': transazione.data,
                            'descrizione': transazione.descrizione,
                            'tipo_transazione': transazione.tipo_transazione,
                            'eseguita' : transazione.eseguita,
                            'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else None,
                            'sottocategoria' : transazione.sotto_categoria.to_dict() if transazione.sotto_categoria != None else None,
                            'conto' : transazione.conto.to_dict(),
                            'conto_arrivo' : transazione.conto_arrivo.to_dict() if transazione.tipo_transazione == 'trasferimento' else None,
                            'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
                             'utente' : (transazione.utente).to_dict(),
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
                                'percentuale_completamento': round(obbiettivo.percentuale_completamento),
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
                    transazioni = BudgetingService.get_transazioni_by_conti(conti).order_by('-data')
                    transazioni_data = [
                        {
                            'id': transazione.id,
                            'importo': transazione.importo,
                            'data': transazione.data,
                            'descrizione': transazione.descrizione,
                            'tipo_transazione': transazione.tipo_transazione,
                            'eseguita' : transazione.eseguita,
                            'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else None,
                            'sottocategoria' : transazione.sotto_categoria.to_dict() if transazione.sotto_categoria != None else None,
                            'conto' : transazione.conto.to_dict(),
                            'conto_arrivo' : transazione.conto_arrivo.to_dict() if transazione.tipo_transazione == 'trasferimento' else None,
                            'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
                            'utente' : (transazione.utente).to_dict(),
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
                            'percentuale_completamento': round(obbiettivo.percentuale_completamento),
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
def savings_section_famiglia(request,id):
    
    utente = UserService.get_utenti_by_user(request.user.pk)
    famiglia = Famiglia.objects.get(pk = id)
    conti = AccountService.get_family_accounts(famiglia)
    if request.method == 'POST':  
        formSavingPlan = NuovoPianoRisparmoFamiglia(request.POST, famiglia = famiglia)
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
            piani = BudgetingService.get_lista_SavingPlan_by_conto(conti)
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



def aggiorna_saldo_totale_transazione_eliminata(utente, data_transazione, importo):
    # Recupera tutti i record di SaldoTotale a partire dalla data della transazione
    saldo_records = SaldoTotale.objects.filter(utente=utente, data_aggiornamento__gte=data_transazione)

    
    for record in saldo_records:
        record.saldo_totale -= importo
        record.save()

@login_required
def transaction_section_famiglia(request, famiglia):
   
    if request.method == 'POST':
     
        utente = UserService.get_utenti_by_user(request.user.pk)
        formTransazione = NuovaTransazioneFamigliaForm(request.POST, utente=request.user, famiglia= famiglia) 
        Fam = Famiglia.objects.get(pk = famiglia)
    
        if formTransazione.is_valid():
            conto = formTransazione.cleaned_data['conto']
            categoria = formTransazione.cleaned_data['categoria']
            obbiettivi_spesa_riguardanti = BudgetingService.get_lista_obbiettivi_spesa_by_categoria(utente,categoria)
           
            match formTransazione.cleaned_data['tipo_transazione']:
                case 'singola':
                    conto_selezionato = formTransazione.cleaned_data['conto']
                    importo = formTransazione.cleaned_data['importo']
                    data = formTransazione.cleaned_data['data']
                    # Scaliamo l'importo dal conto selezionato
                    conto = Conto.objects.get(id=conto_selezionato.id)
                    conto.saldo += importo
                    conto.save()
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
                        eseguita = True,
                    )

                    ChallengeService.aggiorna_sfida(utente,formTransazione.cleaned_data['categoria'],importo)
                    g = ChallengeService.get_family_challenge(Fam)
                    challenge_list = [
                            {
                                'id' : sfida_item.pk,
                                'importo_sfidante' : sfida_item.importo_sfidante,
                                'importo_sfidato' : sfida_item.importo_sfidato,
                                'percentuale_sfidante' : sfida_item.percentuale_sfidante,
                                'percentuale_sfidato' : sfida_item.percentuale_sfidato,
                                'categoria_target' : sfida_item.categoria_target.to_dict(),
                                'sfidante' : sfida_item.sfidante.to_dict(),
                                'sfidato' : sfida_item.sfidato.to_dict(),
                                'descrizione' : sfida_item.descrizione,
                                'data_scadenza' : sfida_item.data_scadenza.strftime('%Y-%m-%d'), 
                                'data_creazione' : sfida_item.data_creazione.strftime('%Y-%m-%d'), 
                                'conclusa' : sfida_item.conclusa,
                            }
                            for sfida_item in g
                        ] 
                   
                    
                    conti = AccountService.get_family_accounts(famiglia)
                    conti_data = [
                        {
                            'id': conto.id,
                            'nome': conto.nome,
                            'tipo': conto.tipo,
                            'saldo': conto.saldo,
                        }
                        for conto in conti
                    ]

                    transazioni = BudgetingService.get_transazioni_by_conti(conti).order_by('-data')
                    
                    transazioni_data = [
                        {
                            'id': transazione.id,
                            'importo': transazione.importo,
                            'data': transazione.data,
                            'descrizione': transazione.descrizione,
                            'tipo_transazione': transazione.tipo_transazione,
                            'eseguita' : transazione.eseguita,
                            'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else None,
                            'sottocategoria' : transazione.sotto_categoria.to_dict() if transazione.sotto_categoria != None else None,
                            'conto' : transazione.conto.to_dict(),
                            'conto_arrivo' : transazione.conto_arrivo.to_dict() if transazione.tipo_transazione == 'trasferimento' else None,
                            'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
                             'utente' : (transazione.utente).to_dict(),
                        }
                        for transazione in transazioni
                    ]
                    
                    if(conto.tipo == 'risparmio'):
                        BudgetingService.ricalcola_lista_piani_risparmio(utente)
                        
                    piani = BudgetingService.get_lista_SavingPlan_by_conto(conti)
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
                    
                    BudgetingService.aggiorna_saldo_totale_dopo_inserimento(utente, data, importo)
                    
                    if obbiettivi_spesa_riguardanti:  
                        for obbiettivo in obbiettivi_spesa_riguardanti:
                             if obbiettivo.data_creazione <= data <= obbiettivo.data_scadenza:
                                obbiettivo.importo_speso += (-importo)
                                obbiettivo.percentuale_completamento = (obbiettivo.importo_speso/ obbiettivo.importo) * 100
                                if(obbiettivo.percentuale_completamento > 100):
                                    obbiettivo.percentuale_completamento = 100
                                if(obbiettivo.percentuale_completamento <= 0):
                                    obbiettivo.percentuale_completamento = 0
                                obbiettivo.save()
                            
                    
                  
                    
                    AccountService.modifica_saldo_totale(utente, importo)


                    saldo_data = SaldoTotale.objects.filter(utente=utente).order_by('data_aggiornamento')
                    labels = [str(saldo.data_aggiornamento) for saldo in saldo_data]  # Date per l'asse X
                    data = [saldo.saldo_totale for saldo in saldo_data]
                    
                    
                    
                    return JsonResponse({
                        'success': True,
                        'conti': conti_data,
                        'transazioni': transazioni_data,
                        "piani_risparmio" : piani_data, 
                        'labels' : labels,
                        'data' : data,
                        'sfide' : challenge_list
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
                        conti = AccountService.get_family_accounts(famiglia)
                        conti_data = [
                            {
                                'id': conto.id,
                                'nome': conto.nome,
                                'tipo': conto.tipo,
                                'saldo': conto.saldo,
                            }
                            for conto in conti
                        ]
                        transazioni = BudgetingService.get_transazioni_by_conti(conti).order_by('-data')
                        transazioni = Transazione.objects.filter(eseguita=True).filter(utente = utente).order_by('-data')
                        transazioni_data = [
                        {
                            'id': transazione.id,
                            'importo': transazione.importo,
                            'data': transazione.data,
                            'descrizione': transazione.descrizione,
                            'tipo_transazione': transazione.tipo_transazione,
                            'eseguita' : transazione.eseguita,
                            'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else None,
                            'sottocategoria' : transazione.sotto_categoria.to_dict() if transazione.sotto_categoria != None else None,
                            'conto' : transazione.conto.to_dict(),
                            'conto_arrivo' : transazione.conto_arrivo.to_dict() if transazione.tipo_transazione == 'trasferimento' else None,
                            'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
                            'utente' : (transazione.utente).to_dict(),
                        }
                        for transazione in transazioni
                        ]
                        
                        if(conto.tipo == 'risparmio'):
                            BudgetingService.ricalcola_lista_piani_risparmio(utente)
                        
                        
                        piani = BudgetingService.get_lista_SavingPlan_by_conto(conti)
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
                        
                        g = ChallengeService.get_family_challenge(Fam)
                        challenge_list = [
                            {
                                'id' : sfida_item.pk,
                                'importo_sfidante' : sfida_item.importo_sfidante,
                                'importo_sfidato' : sfida_item.importo_sfidato,
                                'percentuale_sfidante' : sfida_item.percentuale_sfidante,
                                'percentuale_sfidato' : sfida_item.percentuale_sfidato,
                                'categoria_target' : sfida_item.categoria_target.to_dict(),
                                'sfidante' : sfida_item.sfidante.to_dict(),
                                'sfidato' : sfida_item.sfidato.to_dict(),
                                'descrizione' : sfida_item.descrizione,
                                'data_scadenza' : sfida_item.data_scadenza.strftime('%Y-%m-%d'),
                                'data_creazione' : sfida_item.data_creazione.strftime('%Y-%m-%d'),
                                'conclusa' : sfida_item.conclusa,  
                            }
                            for sfida_item in g
                        ] 
                        return JsonResponse({
                            'success': True,
                            'conti': conti_data,
                            'transazioni': transazioni_data,
                            "piani_risparmio" : piani_data,
                            'sfide' : challenge_list
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
                        data = formTransazione.cleaned_data['data'],
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
                        ChallengeService.aggiorna_sfida(utente,formTransazione.cleaned_data['categoria'],importo)
                        BudgetingService.aggiorna_saldo_totale_dopo_inserimento(utente, data, importo)
                    
        
                        
                        if obbiettivi_spesa_riguardanti:  
                         for obbiettivo in obbiettivi_spesa_riguardanti:
                              if obbiettivo.data_creazione <= data <= obbiettivo.data_scadenza:
                                obbiettivo.importo_speso += (-importo)
                                obbiettivo.percentuale_completamento = (obbiettivo.importo_speso/ obbiettivo.importo) * 100
                                if(obbiettivo.percentuale_completamento > 100):
                                    obbiettivo.percentuale_completamento = 100
                                if(obbiettivo.percentuale_completamento <= 0):
                                    obbiettivo.percentuale_completamento = 0
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
                       
                    conti = AccountService.get_family_accounts(famiglia)
                    conti_data = [
                        {
                            'id': conto.id,
                            'nome': conto.nome,
                            'tipo': conto.tipo,
                            'saldo': conto.saldo,
                        }
                        for conto in conti
                    ]
                    
                    transazioni = BudgetingService.get_transazioni_by_conti(conti).order_by('-data')
                    transazioni_data = [
                        {
                            'id': transazione.id,
                            'importo': transazione.importo,
                            'data': transazione.data,
                            'descrizione': transazione.descrizione,
                            'tipo_transazione': transazione.tipo_transazione,
                            'eseguita' : transazione.eseguita,
                            'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else None,
                            'sottocategoria' : transazione.sotto_categoria.to_dict() if transazione.sotto_categoria != None else None,
                            'conto' : transazione.conto.to_dict(),
                            'conto_arrivo' : transazione.conto_arrivo.to_dict() if transazione.tipo_transazione == 'trasferimento' else None,
                            'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
                             'utente' : (transazione.utente).to_dict(),
                        }
                        for transazione in transazioni
                    ]
                    
                    if(conto.tipo == 'risparmio'):
                        BudgetingService.ricalcola_lista_piani_risparmio(utente)
                        
                    
                    piani = BudgetingService.get_lista_SavingPlan_by_conto(conti)
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
                    g = ChallengeService.get_family_challenge(Fam)
                    challenge_list = [
                            {
                                'id' : sfida_item.pk,
                                'importo_sfidante' : sfida_item.importo_sfidante,
                                'importo_sfidato' : sfida_item.importo_sfidato,
                                'percentuale_sfidante' : sfida_item.percentuale_sfidante,
                                'percentuale_sfidato' : sfida_item.percentuale_sfidato,
                                'categoria_target' : sfida_item.categoria_target.to_dict(),
                                'sfidante' : sfida_item.sfidante.to_dict(),
                                'sfidato' : sfida_item.sfidato.to_dict(),
                                'descrizione' : sfida_item.descrizione,
                                'data_scadenza' : sfida_item.data_scadenza.strftime('%Y-%m-%d'),  
                                'data_creazione' : sfida_item.data_creazione.strftime('%Y-%m-%d'), 
                                'conclusa' : sfida_item.conclusa, 
                            }
                            for sfida_item in g
                        ] 
                    return JsonResponse({
                        'success': True,
                        'conti': conti_data,
                        'transazioni': transazioni_data,
                        "piani_risparmio" : piani_data,
                        'sfide': challenge_list
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
                   

                    
                    conti = AccountService.get_family_accounts(famiglia)
                    conti_data = [
                        {
                            'id': conto.id,
                            'nome': conto.nome,
                            'tipo': conto.tipo,
                            'saldo': conto.saldo,
                        }
                        for conto in conti
                    ]
                    transazioni = BudgetingService.get_transazioni_by_conti(conti).order_by('-data')
                    transazioni_data = [
                        {
                            'id': transazione.id,
                            'importo': transazione.importo,
                            'data': transazione.data,
                            'descrizione': transazione.descrizione,
                            'tipo_transazione': transazione.tipo_transazione,
                            'eseguita' : transazione.eseguita,
                            'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else None,
                            'sottocategoria' : transazione.sotto_categoria.to_dict() if transazione.sotto_categoria != None else None,
                            'conto' : transazione.conto.to_dict(),
                            'conto_arrivo' : transazione.conto_arrivo.to_dict() if transazione.tipo_transazione == 'trasferimento' else None,
                            'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
                            'utente' : (transazione.utente).to_dict(),
                        }
                        for transazione in transazioni
                    ]

                    if(conto.tipo == 'risparmio'):
                        BudgetingService.ricalcola_lista_piani_risparmio(utente)
                        
                    
                    
                    piani = BudgetingService.get_lista_SavingPlan_by_conto(conti)
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

                    g = ChallengeService.get_family_challenge(Fam)
                    challenge_list = [
                            {
                                'id' : sfida_item.pk,
                                'importo_sfidante' : sfida_item.importo_sfidante,
                                'importo_sfidato' : sfida_item.importo_sfidato,
                                'percentuale_sfidante' : sfida_item.percentuale_sfidante,
                                'percentuale_sfidato' : sfida_item.percentuale_sfidato,
                                'categoria_target' : sfida_item.categoria_target.to_dict(),
                                'sfidante' : sfida_item.sfidante.to_dict(),
                                'sfidato' : sfida_item.sfidato.to_dict(),
                                'descrizione' : sfida_item.descrizione,
                                'data_scadenza' : sfida_item.data_scadenza.strftime('%Y-%m-%d'),  
                                'data_creazione' : sfida_item.data_creazione.strftime('%Y-%m-%d'), 
                                'conclusa' : sfida_item.conclusa, 
                            }
                            for sfida_item in g
                        ] 
                    return JsonResponse({
                        'success': True,
                        'conti': conti_data,
                        'transazioni': transazioni_data,
                        "piani_risparmio" : piani_data,
                        'sfide' : challenge_list
                    })
        else:
            return JsonResponse({'success': False, 'errors': formTransazione.errors}, status=400)

  


@login_required
def elimina_transazione(request, id):
    if request.method == 'POST':
        transazione = Transazione.objects.get(pk = id)
        data_transazione = transazione.data
        categoria = transazione.categoria
        utente = UserService.get_utenti_by_user(request.user.pk)
        conti = AccountService.get_conti_utente(utente.pk)
        conto = Conto.objects.get(pk = transazione.conto.pk)
        conto.saldo -= transazione.importo
        conto.save()
        aggiorna_saldo_totale_transazione_eliminata(utente, data_transazione, transazione.importo)
        
        if conto.tipo == 'risparmio':  # Assicurati di avere un modo per identificare il tipo di conto
            piani = BudgetingService.get_lista_SavingPlan_byConto(conto.id)
            for piano in piani:
                BudgetingService.ricalcola_percentuale_completamento_pianoRisparmio(request, piano.id)

       
        
        obiettivi = BudgetingService.get_lista_Obbiettivi_Spesa(utente).filter(
            data_scadenza__gte=data_transazione,
            data_creazione__lte=data_transazione,
            categoria_target= categoria,
        )

        for obbiettivo in obiettivi:
            
            obbiettivo.importo_speso += transazione.importo 
            obbiettivo.save()# Aggiorna l'importo speso
            BudgetingService.ricalcola_percentuale_completamento_obbiettivoSpesa(request, obbiettivo.id)  # Ricalcola la percentuale di completamento

        aggiorna_saldo_totale_transazione_eliminata(utente, data_transazione, transazione.importo)

        ChallengeService.aggiorna_sfida(utente,transazione.categoria,(-transazione.importo))
        
        transazione.delete()  
        
        lista_transazioni = BudgetingService.get_transazioni_by_conti(conti).order_by('-data')
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
                'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else 'Trasferimento',
                'sottocategoria' : transazione.sotto_categoria.to_dict() if transazione.sotto_categoria != None else None,
                'utente' : (transazione.utente).to_dict(),
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
            persone_intestate.delete() 
            
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
        
            percentuale = BudgetingService.ricalcola_percentuale_completamento_pianoRisparmio(request,id)

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


@login_required
def crea_famiglia(request, nome_famiglia):
    
    if request.method == 'POST':
        new_family = Famiglia(
            nome_famiglia=nome_famiglia,
            data_creazione=timezone.now()
        )
        new_family.save()

        utente = Utente.objects.get(user_profile=request.user)
        utente.famiglia.add(new_family)

        return JsonResponse({'success': True})  # Return a JSON response indicating success

    return JsonResponse({'success': False}, status=400)  # Handle other methods or errors


@login_required
def createFamChallenge(request, famiglia):
    print(request.user.pk)
    utente = UserService.get_utenti_by_user(request.user.pk) 
    print(utente)
    form = NuovaSfidaFamigliare(request.POST,utente= utente, famiglia= famiglia)
    
    fam = Famiglia.objects.get(pk = famiglia)
    
    if form.is_valid():
        SfidaFamigliare.objects.create(
            sfidante=utente,
            sfidato=form.cleaned_data['sfidato'],
            conclusa= False,
            data_creazione=timezone.now().date(),
            data_scadenza=form.cleaned_data['data_scadenza'],
            importo_sfidante=0,
            importo_sfidato=0,
            descrizione=form.cleaned_data['descrizione'],
            categoria_target=form.cleaned_data['categoria_target'],
            famiglia=fam,
        )
        g = ChallengeService.get_family_challenge(fam)
        challenge_list = [
                            {
                                'id' : sfida_item.pk,
                                'importo_sfidante' : sfida_item.importo_sfidante,
                                'importo_sfidato' : sfida_item.importo_sfidato,
                                'percentuale_sfidante' : sfida_item.percentuale_sfidante,
                                'percentuale_sfidato' : sfida_item.percentuale_sfidato,
                                'categoria_target' : sfida_item.categoria_target.to_dict(),
                                'sfidante' : sfida_item.sfidante.to_dict(),
                                'sfidato' : sfida_item.sfidato.to_dict(),
                                'descrizione' : sfida_item.descrizione,
                                'data_scadenza' : sfida_item.data_scadenza.strftime('%Y-%m-%d'),  
                                'data_creazione' : sfida_item.data_creazione.strftime('%Y-%m-%d'), 
                                'conclusa' : sfida_item.conclusa, 
                            }
                            for sfida_item in g
                        ] 
        return JsonResponse({'valid': True, 'sfide' : challenge_list})
    
    return JsonResponse({'valid': False, 'errors': form.errors}, status=400) 

        
    
@login_required
def eliminaChallenge(request, id):
    if request.method == 'POST':
        try:
            sfida = SfidaFamigliare.objects.get(pk=id)
            
            sfida.delete()
            
            response_data = {
                'success': True,
                'message': 'Challenge successfully deleted.'
            }
        except Conto.DoesNotExist:
            response_data = {
                'success': False,
                'message': 'Challenge doesn\'t exist'
            }
        
        return JsonResponse(response_data)
    else:
        return JsonResponse({'success': False, 'message': 'Metodo non permesso.'}, status=405)

@login_required
def modificaChallenge(request, id, new_date):
    if request.method == 'POST':
        try:
            
            Challenge = (SfidaFamigliare.objects.get(pk = id))
            
            Challenge.data_scadenza = new_date
            
            Challenge.save()
            
            
            response_data = {
                'success': True,
            }
            
        except Challenge.DoesNotExist:
            response_data = {
                'success': False,
            }
        
        return JsonResponse(response_data)
    else:
        return JsonResponse({'success': False}, status=405)




@login_required
def unisciti_famiglia(request, codice):
    if request.method == 'POST':
        famiglia = Famiglia.objects.filter(codice=codice).first()
        
        if famiglia:
            conti = AccountService.get_family_accounts(famiglia)
            utente = UserService.get_utenti_by_user(request.user.pk)
            if famiglia in utente.famiglia.all():
                return JsonResponse({'success': False}, status=400)
            
            utente.famiglia.add(famiglia)
            utente.save()
            famiglia.numero_partecipanti += 1
            famiglia.save()
            
           
        
            for conto in conti:
                IntestazioniConto.objects.create(
                    conto=conto,
                    utente=utente,
                    data_intestazione=timezone.now().date()
                )
            return JsonResponse({'success': True})
       
        return JsonResponse({'success': False}, status=400)
    

    return JsonResponse({'success': False}, status=400)

@login_required
def investments(request):
    utente = UserService.get_utenti_by_user(request.user.pk)
    conti = AccountService.get_conti_investimento_utente(utente.pk)
    formTransazione = NuovoInvestimentoForm(utente=request.user)
    AccountService.calcola_saldo_totale_investimenti(utente)
    utente = UserService.get_utenti_by_user(request.user.pk)
    saldo_data = SaldoTotaleInvestimenti.objects.filter(utente=utente).order_by('data_aggiornamento')
    labels = [str(saldo.data_aggiornamento) for saldo in saldo_data]  # Date per l'asse X
    data = [saldo.saldo_totale for saldo in saldo_data]
    aggiorna_posizioni_investimenti(request)
    context = { "data" : data, "labels": labels, "conti" : conti, "formTransazione" : formTransazione}
    return render(request, 'investments/homepageInvest.html', context)


def get_company_data(request, company_name):
    api_key = os.getenv('FINHUB_API_KEY')
    url = f'https://finnhub.io/api/v1/search?q={company_name}&token={api_key}'

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
        
        # Filtrare solo le azioni comuni (Common Stock) senza suffissi
        filtered_results = [
            company for company in data.get('result', [])
            if 'Common Stock' in company.get('type', '') and '.' not in company['displaySymbol']
        ]

        # Ordinare i risultati in base al simbolo (opzionale)
        filtered_results.sort(key=lambda x: x['displaySymbol'])  # Ordinamento semplice

        return JsonResponse({'result': filtered_results})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_exchange_rate():
    # Funzione per ottenere il tasso di cambio USD to EUR
    url = 'https://api.exchangerate-api.com/v4/latest/USD'  # API per il tasso di cambio
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return data['rates']['EUR']  # Restituisce il tasso di cambio per EUR
    except urllib.error.URLError as e:
        return None  # Gestione dell'errore
    
def get_stock_data(request, symbol):
    api_key = settings.ALPHA_VANTAGE_API_KEY
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}'
    
    try:
        # Effettua la richiesta usando urllib
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())

        # Gestione dell'errore
        if 'Error Message' in data:
            return JsonResponse({'error': 'Invalid symbol'}, status=400)

        return JsonResponse(data)

    except urllib.error.URLError as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_latest_price_in_euro(request, symbol):
    # Richiama la funzione get_stock_data per ottenere i dati delle azioni
    stock_data_response = get_stock_data(request, symbol)

    # Controlla se ci sono errori nella risposta
    if isinstance(stock_data_response, JsonResponse) and stock_data_response.status_code != 200:
        return stock_data_response  # Restituisce errore se presente

    # Estrai i dati delle azioni dalla risposta JSON
    stock_data = json.loads(stock_data_response.content)  # Usa content per ottenere i dati

    # Controlla se la chiave 'Time Series (Daily)' è presente
    if 'Time Series (Daily)' not in stock_data:
        return JsonResponse({'error': 'No time series data available for this symbol.'}, status=400)

    # Estrai l'ultimo prezzo disponibile
    latest_date = next(iter(stock_data['Time Series (Daily)']))
    
    closing_price_usd = float(stock_data['Time Series (Daily)'][latest_date]['4. close'])

    # Ottieni il tasso di cambio USD to EUR
    exchange_rate = get_exchange_rate()

    if exchange_rate is None:
        return JsonResponse({'error': 'Unable to fetch exchange rate'}, status=500)

    # Calcola il prezzo in euro
    closing_price_eur = closing_price_usd * exchange_rate

    # Restituisci il prezzo in euro formattato
    response_data = {
        'symbol': symbol,
        'closing_price_usd': f"${closing_price_usd:.2f}",
        'closing_price_eur': f"€{closing_price_eur:.2f}"
    }

    return JsonResponse(response_data)

def aggiorna_posizioni_investimenti(request):
    utente = UserService.get_utenti_by_user(request.user.pk)
    posizioni = AccountService.get_posizioni(utente=utente)

    for posizione in posizioni:
        # Richiama il prezzo attuale in euro
        prezzo_attuale_response = get_latest_price_in_euro(request, posizione.ticker)
        print("ciao")
        # Controlla se ci sono errori nella risposta
        if isinstance(prezzo_attuale_response, JsonResponse) and prezzo_attuale_response.status_code != 200:
            return prezzo_attuale_response  

        print("ehi")
        prezzo_attuale_data = prezzo_attuale_response.json()
        prezzo_attuale = float(prezzo_attuale_data['closing_price_eur'].replace('€', '').replace(',', '.'))

     
        posizione.saldo_totale = posizione.numero_azioni * prezzo_attuale
        posizione.differenza = posizione.saldo_totale - posizione.saldo_investito

        # Salva le modifiche alla posizione nel database
        posizione.save()

    return JsonResponse({'message': 'Posizioni aggiornate con successo'}, status=200)

@login_required
def investment_section(request, symbol, nome_azienda):
    if request.method == 'POST':
        utente = UserService.get_utenti_by_user(request.user.pk)
        formTransazione = NuovoInvestimentoForm(request.POST, utente=request.user) 
        
        if formTransazione.is_valid():
            conto_id = formTransazione.cleaned_data['conto']
            conto = Conto.objects.get(id=conto_id.id)
            importo = -(formTransazione.cleaned_data['numero_azioni']*formTransazione.cleaned_data['prezzo_azione'])
            conto.saldo += Decimal(importo)
            conto.save()
            
            Transazione.objects.create(
                        conto=conto,
                        importo=importo,
                        data=  timezone.now().date(),
                        descrizione= formTransazione.cleaned_data['descrizione'],
                        tipo_transazione= CategoriaTransazione.INVESTIMENTO,
                        utente=  utente, 
                        eseguita = True,
                        ticker = symbol,
                        prezzo_azione = formTransazione.cleaned_data['prezzo_azione'],
                        numero_azioni = formTransazione.cleaned_data['numero_azioni'],
                    )

            conti = AccountService.get_conti_investimento_utente(utente.pk)
            conti_data = [
                        {
                            'id': conto.id,
                            'nome': conto.nome,
                            'tipo': conto.tipo,
                            'saldo': conto.saldo,
                        }
                        for conto in conti
                ]

            transazioni = BudgetingService.get_transazioni_by_conti(conti).order_by('-data')
            transazioni_data = [
                        {
                            'id': transazione.id,
                            'importo': transazione.importo,
                            'data': transazione.data,
                            'descrizione': transazione.descrizione,
                            'tipo_transazione': transazione.tipo_transazione,
                            'eseguita' : transazione.eseguita,
                            'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else None,
                            'sottocategoria' : transazione.sotto_categoria.to_dict() if transazione.sotto_categoria != None else None,
                            'conto' : transazione.conto.to_dict(),
                            'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
                            'utente' : (transazione.utente).to_dict(),
                            'ticker' : symbol,
                            'prezzo_azione' : transazione.prezzo_azione,
                            'numero_azioni' : transazione.numero_azioni,
                        }
                        for transazione in transazioni
                    ]
                    
                    
            
            AccountService.modifica_saldo_totale(utente, Decimal(importo))
            AccountService.modifica_saldo_totale_investimenti(utente, Decimal(importo))
            AccountService.registra_posizione_investimento(utente, conto, symbol,  formTransazione.cleaned_data['numero_azioni'], formTransazione.cleaned_data['prezzo_azione'], nome_azienda)
            
            saldo_data = SaldoTotaleInvestimenti.objects.filter(utente=utente).order_by('data_aggiornamento')
            labels = [str(saldo.data_aggiornamento) for saldo in saldo_data]  # Date per l'asse X
            data = [saldo.saldo_totale for saldo in saldo_data]
                    
            return JsonResponse({
                        'success': True,
                        'conti': conti_data,
                        'transazioni': transazioni_data,
                        'labels' : labels,
                        'data' : data,
                    })
  