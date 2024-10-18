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
    ChallengeService.concludi_sfida(utente)
    today = date.today()
    posizione_oggi_esiste = SaldoTotaleInvestimenti.objects.filter(data_aggiornamento=today, utente=utente).exists()
    if not posizione_oggi_esiste:
        aggiorna_posizioni_investimenti(request)
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
                    'data': transazione.data.strftime('%Y-%m-%d'),  
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
                liquidita = form.cleaned_data['saldo'],
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
    categorie, importi = BudgetingService.get_spese_per_categoria(utente)

    categorie_ultimo_mese, importi_ultimo_mese = BudgetingService.get_spese_per_categoria_ultimo_mese(utente)
    
    labels = [str(saldo.data_aggiornamento) for saldo in saldo_data]  
    data = [saldo.saldo_totale for saldo in saldo_data]

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
            'data': transazione.data.strftime('%Y-%m-%d'),  
            'tipo_transazione': transazione.tipo_transazione,
            'conto' :  (Conto.objects.get(pk = transazione.conto.pk )).to_dict(),
            'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
            'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else 'Trasferimento',
            'sottocategoria' : transazione.sotto_categoria.to_dict() if transazione.sotto_categoria != None else None,
            'utente' : (transazione.utente).to_dict(),
            'ticker' : transazione.ticker,
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
                saldo=(form.cleaned_data['saldo']),
                liquidita = form.cleaned_data['saldo'],
            )
            IntestazioniConto.objects.create(
                conto=conto,
                utente=utente,
                data_intestazione=timezone.now().date()
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
                'obbiettivi_spesa_json' : obbiettivi_spesa_data, 'utente' : utente,
                'categorie': categorie, 'importi': importi,
                'categorie_ultimo_mese': categorie_ultimo_mese, 'importi_ultimo_mese': importi_ultimo_mese,
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
                    labels = [str(saldo.data_aggiornamento) for saldo in saldo_data] 
                    data = [saldo.saldo_totale for saldo in saldo_data]
                    
                    categorie, importi = BudgetingService.get_spese_per_categoria(utente)
                    labels_spese = [str(categoria) for categoria in categorie]
                    data_spese = [ importo for importo in importi]
                    
                    categorie1, importi1 = BudgetingService.get_spese_per_categoria(utente)
                    labels_spese_ultimo_mese = [str(categoria) for categoria in categorie1]
                    data_spese_ultimo_mese = [ importo for importo in importi1]
                    
                
                    return JsonResponse({
                        'success': True,
                        'conti': conti_data,
                        'transazioni': transazioni_data,
                        "piani_risparmio" : piani_data, 
                        'obbiettivi_spesa' : Obbiettivi_data,
                        'labels' : labels,
                        'data' : data,
                        'categorie': categorie, 'importi': importi,
                        'labels_spese' : labels_spese,
                        'data_spese' : data_spese,
                        'labels_spese_ultimo_mese' : labels_spese_ultimo_mese,
                        'data_spese_ultimo_mese' : data_spese_ultimo_mese,
                        
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
                        labels = [str(saldo.data_aggiornamento) for saldo in saldo_data] 
                        data = [saldo.saldo_totale for saldo in saldo_data]
                        categorie, importi = BudgetingService.get_spese_per_categoria(utente)
                        labels_spese = [str(categoria) for categoria in categorie]
                        data_spese = [ importo for importo in importi]
                        categorie1, importi1 = BudgetingService.get_spese_per_categoria(utente)
                        labels_spese_ultimo_mese = [str(categoria) for categoria in categorie1]
                        data_spese_ultimo_mese = [ importo for importo in importi1]
                        return JsonResponse({
                            'success': True,
                            'conti': conti_data,
                            'transazioni': transazioni_data,
                            "piani_risparmio" : piani_data,
                            'obbiettivi_spesa' : Obbiettivi_data,
                            'labels' : labels,
                            'data' : data,
                            'categorie': categorie, 'importi': importi,
                            'labels_spese' : labels_spese,
                            'data_spese' : data_spese,
                            'labels_spese_ultimo_mese' : labels_spese_ultimo_mese,
                            'data_spese_ultimo_mese' : data_spese_ultimo_mese,
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
                    labels = [str(saldo.data_aggiornamento) for saldo in saldo_data]  
                    data = [saldo.saldo_totale for saldo in saldo_data]
                    categorie, importi = BudgetingService.get_spese_per_categoria(utente)
                    labels_spese = [str(categoria) for categoria in categorie]
                    data_spese = [ importo for importo in importi]
                    categorie1, importi1 = BudgetingService.get_spese_per_categoria(utente)
                    labels_spese_ultimo_mese = [str(categoria) for categoria in categorie1]
                    data_spese_ultimo_mese = [ importo for importo in importi1]
                    
                    return JsonResponse({
                        'success': True,
                        'conti': conti_data,
                        'transazioni': transazioni_data,
                        "piani_risparmio" : piani_data,
                        'obbiettivi_spesa' : Obbiettivi_data,
                        'labels' : labels,
                        'data' : data,
                        'categorie': categorie, 'importi': importi,
                        'labels_spese' : labels_spese,
                        'data_spese' : data_spese,
                        'labels_spese_ultimo_mese' : labels_spese_ultimo_mese,
                        'data_spese_ultimo_mese' : data_spese_ultimo_mese,
                    })
                case 'trasferimento':
                    conto_partenza = formTransazione.cleaned_data['conto']
                    conto_destinazione = formTransazione.cleaned_data['conto_arrivo']
                    importo = formTransazione.cleaned_data['importo']

                # A -> B
                    conto = Conto.objects.get(id=conto_partenza.id)
                    conto.saldo -= importo
                    conto.liquidita -= importo
                        
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
                        conto_arrivo = conto_destinazione
                        
                    )
                
                 # B -> A
                    conto = Conto.objects.get(id=conto_destinazione.id)
                    conto.saldo += importo
                    conto.liquidita += importo
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
                    labels = [str(saldo.data_aggiornamento) for saldo in saldo_data]  
                    data = [saldo.saldo_totale for saldo in saldo_data]
                    categorie, importi = BudgetingService.get_spese_per_categoria(utente)
                    labels_spese = [str(categoria) for categoria in categorie]
                    data_spese = [ importo for importo in importi]
                    categorie1, importi1 = BudgetingService.get_spese_per_categoria(utente)
                    labels_spese_ultimo_mese = [str(categoria) for categoria in categorie1]
                    data_spese_ultimo_mese = [ importo for importo in importi1]
                    
                    return JsonResponse({
                        'success': True,
                        'conti': conti_data,
                        'transazioni': transazioni_data,
                        "piani_risparmio" : piani_data,
                        'obbiettivi_spesa' : Obbiettivi_data,
                        'labels' : labels,
                        'data' : data,
                        'categorie': categorie, 'importi': importi,
                        'labels_spese' : labels_spese,
                        'data_spese' : data_spese,
                        'labels_spese_ultimo_mese' : labels_spese_ultimo_mese,
                        'data_spese_ultimo_mese' : data_spese_ultimo_mese,
                    })
        else:
            return JsonResponse({'success': False, 'errors': formTransazione.errors}, status=400)

   
    
    utente = UserService.get_utenti_by_user(request.user.id)
    conti = AccountService.get_conti_utente(utente.pk)

    formTransazione = NuovaTransazioneForm(utente=request.user) 
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
                    labels = [str(saldo.data_aggiornamento) for saldo in saldo_data] 
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
        
        if conto.tipo == 'risparmio':  
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
            obbiettivo.save()
            BudgetingService.ricalcola_percentuale_completamento_obbiettivoSpesa(request, obbiettivo.id) 

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
                'data': transazione.data.strftime('%Y-%m-%d'), 
                'tipo_transazione': transazione.tipo_transazione,
                'conto_id' :  float(Conto.objects.get(pk = transazione.conto.pk ).pk),
                'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
                'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else 'Trasferimento',
                'sottocategoria' : transazione.sotto_categoria.to_dict() if transazione.sotto_categoria != None else None,
                'utente' : (transazione.utente).to_dict(),
                'ticker' : transazione.ticker,
            })
            
       
        return JsonResponse(transazioni_serializzate, safe=False)


@login_required
def obbiettivoSpesa_section(request):
        utente = UserService.get_utenti_by_user(request.user.pk)
        
        if request.method == 'POST':  
            formSpendingGoal = ObbiettivoSpesaForm(request.POST)
            if formSpendingGoal.is_valid():
                tipo = formSpendingGoal.cleaned_data['tipo']

              
                data_creazione = timezone.now().date()

                if tipo == 'mensile':
                    data_scadenza = data_creazione + timedelta(days=30)  
                elif tipo == 'trimestrale':
                    data_scadenza = data_creazione + timedelta(days=90) 
                elif tipo == 'semestrale':
                    data_scadenza = data_creazione + timedelta(days=180)
                elif tipo == 'annuale':
                    data_scadenza = data_creazione + timedelta(days=365)  
                else:
                    data_scadenza = data_creazione 

           
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
         
        
           
            piano.obbiettivo = Decimal(new_obbiettivo)
            piano.save()
        
            percentuale = BudgetingService.ricalcola_percentuale_completamento_pianoRisparmio(request,id)

            percentuale_troncata = round(percentuale, 2)
            
            response_data = {
                'success': True,
                'percentuale': percentuale_troncata,
            }
        except ObjectDoesNotExist:  
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
            obbiettivo = (BudgetingService.get_lista_Obbiettivi_Spesa(utente)).get(pk = id)
            obbiettivo.importo = Decimal(new_obbiettivo)
            obbiettivo.save()
        
            
            percentuale = BudgetingService.ricalcola_percentuale_completamento_obbiettivoSpesa(request,id)
            percentuale_troncata = round(percentuale, 2)
            
            response_data = {
                'success': True,
                'percentuale': percentuale_troncata,
            }
        except ObjectDoesNotExist:  
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

        return JsonResponse({'success': True})  

    return JsonResponse({'success': False}, status=400) 

@login_required
def createFamChallenge(request, famiglia):
    utente = UserService.get_utenti_by_user(request.user.pk) 
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
    formTransazione = NuovoInvestimentoForm(utente=request.user)
    formVendita = NuovaVenditaForm(utente = request.user)
    AccountService.calcola_saldo_totale_investimenti(utente)
    utente = UserService.get_utenti_by_user(request.user.pk)
    saldo_data = SaldoTotaleInvestimenti.objects.filter(utente=utente).order_by('data_aggiornamento')
    labels = [str(saldo.data_aggiornamento) for saldo in saldo_data]  
    data = [saldo.saldo_totale for saldo in saldo_data]
    posizione_aperta_list = AccountService.get_posizioni(utente)
    conti = AccountService.get_conti_investimento_utente(utente.pk)
    conti_data = [
                        {
                            'id': conto.id,
                            'nome': conto.nome,
                            'tipo': conto.tipo,
                            'saldo': float(conto.saldo),
                            'liquidita' : float(conto.liquidita),
                        }
                        for conto in conti
                ]
    lista_transazioni = BudgetingService.get_transazioni_by_conti(conti).order_by('-data')
    transazioni_serializzate = []
    for transazione in lista_transazioni:
            transazioni_serializzate.append({
                'id': transazione.id,
                'descrizione': transazione.descrizione if transazione.delete != None else '',
                'importo': float(transazione.importo),  
                'data': transazione.data.strftime('%Y-%m-%d'), 
                'tipo_transazione': transazione.tipo_transazione,
                'conto_id' :  float(Conto.objects.get(pk = transazione.conto.pk ).pk),
                'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
                'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else 'Trasferimento',
                'sottocategoria' : transazione.sotto_categoria.to_dict() if transazione.sotto_categoria != None else None,
                'utente' : (transazione.utente).to_dict(),
                'ticker' : transazione.ticker,
                
            })
    context = { "data" : data, "labels": labels, "conti" : conti,
               "formTransazione" : formTransazione, 'posizione_aperta_list' : posizione_aperta_list,
               'formVendita' : formVendita,
                'conti_json' : json.dumps(conti_data),
                "transazioni_serializzate": json.dumps(transazioni_serializzate),}
    return render(request, 'investments/homepageInvest.html', context)

@login_required
def get_company_data(request, company_name):
    api_key = os.getenv('FINHUB_API_KEY')
    url = f'https://finnhub.io/api/v1/search?q={company_name}&token={api_key}'

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
        
        
        filtered_results = [
            company for company in data.get('result', [])
            if 'Common Stock' in company.get('type', '') and '.' not in company['displaySymbol']
        ]


        filtered_results.sort(key=lambda x: x['displaySymbol']) 

        return JsonResponse({'result': filtered_results})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def get_exchange_rate():
   
    url = 'https://api.exchangerate-api.com/v4/latest/USD'  # API 
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return data['rates']['EUR']  
    except urllib.error.URLError as e:
        return None 

@login_required   
def get_stock_data(request, symbol):
    api_key = settings.ALPHA_VANTAGE_API_KEY
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}'
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
        print(data)  #verifica 25 richieste al giorno
        if 'Error Message' in data:
            return JsonResponse({'error': 'Invalid symbol'}, status=400)

        return JsonResponse(data)

    except urllib.error.URLError as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_latest_price_in_euro(request, symbol):
    
    
    stock_data_response = get_stock_data(request, symbol)
    #print(stock_data_response)
    if isinstance(stock_data_response, JsonResponse) and stock_data_response.status_code != 200:
        return stock_data_response  

   
    stock_data = json.loads(stock_data_response.content)  

   
    if 'Time Series (Daily)' not in stock_data:
        return JsonResponse({'error': 'No time series data available for this symbol.'}, status=400)

    
    latest_date = next(iter(stock_data['Time Series (Daily)']))
    
    closing_price_usd = float(stock_data['Time Series (Daily)'][latest_date]['4. close'])

    
    exchange_rate = get_exchange_rate()
   
    if exchange_rate is None:
        return JsonResponse({'error': 'Unable to fetch exchange rate'}, status=500)

    
    closing_price_eur = closing_price_usd * exchange_rate
    

   
    response_data = {
        'symbol': symbol,
        'closing_price_usd': f"${closing_price_usd:.2f}",
        'closing_price_eur': f"{closing_price_eur:.2f}"
    }

    return JsonResponse(response_data)

@login_required
def aggiorna_posizioni_investimenti(request):
    utente = UserService.get_utenti_by_user(request.user.pk)
    posizioni = AccountService.get_posizioni(utente=utente)
    
    for posizione in posizioni:
        prezzo_attuale_response = get_latest_price_in_euro(request, posizione.ticker)
        
        if isinstance(prezzo_attuale_response, JsonResponse) and prezzo_attuale_response.status_code != 200:
            return prezzo_attuale_response  
        
        prezzo_attuale_data = prezzo_attuale_response.content
        json_string = prezzo_attuale_data.decode('utf-8')
        prezzo_attuale_dict = json.loads(json_string)
        closing_price_eur = prezzo_attuale_dict['closing_price_eur']
        closing_price_decimal = Decimal(closing_price_eur)
       

        posizione.saldo_totale = posizione.numero_azioni * closing_price_decimal
        posizione.differenza = posizione.saldo_totale - posizione.saldo_investito

        posizione.save()
    
    conti = AccountService.get_conti_investimento_utente(utente)
    totale_posizioni = 0
    for conto in conti:
        totale_posizioni = 0
        posizioni = PosizioneAperta.objects.filter(conto = conto)
        for posizione in posizioni:
            totale_posizioni += posizione.saldo_totale
        conto.saldo = conto.liquidita + totale_posizioni
        conto.save()
    
    
            
    
    AccountService.calcola_saldo_totale(utente)
    AccountService.calcola_saldo_totale_investimenti(utente)
   
 
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
            conto.liquidita += Decimal(importo)
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

             
            
            AccountService.registra_posizione_investimento(utente, conto, symbol,  formTransazione.cleaned_data['numero_azioni'], formTransazione.cleaned_data['prezzo_azione'], nome_azienda)
            aggiorna_posizioni_investimenti(request) #ogni mattina da reinserire
            
             
            conti = AccountService.get_conti_investimento_utente(utente.pk)
            conti_data = [
                        {
                            'id': conto.id,
                            'nome': conto.nome,
                            'tipo': conto.tipo,
                            'saldo': float(conto.saldo),
                            'liquidita' : float(conto.liquidita),
                        }
                        for conto in conti
                ]
            

            transazioni = BudgetingService.get_transazioni_by_conti(conti).order_by('-data')
            transazioni_data = [
                        {
                            'id': float(transazione.id),
                            'importo': float(transazione.importo),
                            'data': transazione.data.strftime('%Y-%m-%d'),
                            'descrizione': transazione.descrizione,
                            'tipo_transazione': transazione.tipo_transazione,
                            'conto_id' :  float(Conto.objects.get(pk = transazione.conto.pk ).pk),
                            'eseguita' : transazione.eseguita,
                            'categoria' : transazione.categoria.to_dict() if transazione.categoria != None else None,
                            'sottocategoria' : transazione.sotto_categoria.to_dict() if transazione.sotto_categoria != None else None,
                            'conto' : transazione.conto.to_dict(),
                            'nome_conto' : (Conto.objects.get(pk = transazione.conto.pk )).nome,
                            'utente' : (transazione.utente).to_dict(),
                            'ticker' : symbol,
                            'prezzo_azione' : float(transazione.prezzo_azione),
                            'numero_azioni' : float(transazione.numero_azioni),
                        }
                        for transazione in transazioni
                    ]
            
            posizioni_utente = AccountService.get_posizioni(utente=utente)   
            posizioni_data = [
                {
                    'id' : posizione.id,
                    'nome_azienda' : posizione.nome_azienda,
                    'conto' : posizione.conto.to_dict(),
                    'numero_azioni' : posizione.numero_azioni,
                    'saldo_totale' : posizione.saldo_totale,
                    'saldo_investito' : posizione.saldo_investito,
                    'pmc' : posizione.pmc,
                    'differenza' : posizione.differenza,
                    'ticker' : posizione.ticker,
                }
                for posizione in posizioni_utente
            ] 
            saldo_data = SaldoTotaleInvestimenti.objects.filter(utente=utente).order_by('data_aggiornamento')
            labels = [str(saldo.data_aggiornamento) for saldo in saldo_data]  
            data = [saldo.saldo_totale for saldo in saldo_data]
                    
            return JsonResponse({
                        'success': True,
                        'conti': conti_data,
                        'transazioni': transazioni_data,
                        'labels' : labels,
                        'data' : data,
                        'posizioni' : posizioni_data,
                        'conti_json' : json.dumps(conti_data),
                    })
        return JsonResponse({'success' : False,'errors': formTransazione.errors})

@login_required
def sell_section(request):
    if request.method == 'POST':
        utente = UserService.get_utenti_by_user(request.user.pk)
        formVendinta = NuovaVenditaForm(request.POST, utente=request.user) 
        
        if formVendinta.is_valid():
            posizione_id = formVendinta.cleaned_data['nome_azienda']
            posizione_obj = PosizioneAperta.objects.get(pk = posizione_id)
            numero_azioni = formVendinta.cleaned_data['numero_azioni']
            ticker = posizione_obj.ticker
            conto = posizione_obj.conto
            pmc = posizione_obj.pmc
            #print(ticker)
            
            prezzo_attuale_data = (get_latest_price_in_euro(request, ticker)).content
            #print(prezzo_attuale_data)
            json_string = prezzo_attuale_data.decode('utf-8')
            #print(json_string)
            prezzo_attuale_dict = json.loads(json_string)
            #print(prezzo_attuale_dict)
            closing_price_eur = prezzo_attuale_dict['closing_price_eur']
            #print(closing_price_eur)
            prezzo = Decimal(closing_price_eur)
            AccountService.registra_posizione_vendita(utente, conto, ticker, numero_azioni, prezzo,pmc)
            return JsonResponse({'message': 'Posizioni aggiornate con successo', 'success' : True}, status=200)
        return JsonResponse({'success' : False,'errors': formVendinta.errors})
    
@login_required
def toolkit_switch(request):
    return render(request, 'toolkit/toolkit.html')


@login_required
def update_profile(request):
    utente = UserService.get_utenti_by_user(request.user.pk)

    if request.method == "POST":
    
        username = request.POST.get('username')
        password = request.POST.get('password')
        telefono = request.POST.get('telefono')
        nome = request.POST.get('nome')
        cognome = request.POST.get('cognome')
        data_di_nascita = request.POST.get('data_di_nascita')
        indirizzo = request.POST.get('indirizzo')
        sesso = request.POST.get('sesso')

        utente.username = username
        if password: 
            request.user.set_password(password)
            utente.password = password
        
        request.user.save()
        utente.telefono = telefono
        utente.nome = nome
        utente.cognome = cognome
        utente.data_di_nascita = data_di_nascita
        utente.indirizzo = indirizzo
        utente.sesso = sesso
        
       
        utente.save()

       
        updated_data = {
            'username': utente.username,
            'telefono': utente.telefono,
            'nome': utente.nome,
            'cognome': utente.cognome,
            'data_di_nascita': utente.data_di_nascita,
            'indirizzo': utente.indirizzo,
            'sesso': utente.sesso,
        }
        return JsonResponse(updated_data)
    
    context = {"utente": utente}
    return render(request, 'toolkit/profile.html', context)
