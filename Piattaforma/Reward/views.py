import json
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.http import JsonResponse
from Users.services import *
from Reward.services import *
from django.http import JsonResponse


def shop_view(request):
    
    utente = UserService.get_utenti_by_user(request.user.pk)
    premi = RewardService.get_premi().order_by('valore')  
    context = { 'utente': utente, "premi" : premi}
    return render(request, 'gift_card.html', context)

def purchase_item(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        item_name = data.get('item')
        item_price = data.get('price')
        print(item_name)
        print(item_price)
        try:
            
            utente = UserService.get_utenti_by_user(request.user.pk)

           
            premio = Premio.objects.get(nome=item_name, costo_monete=item_price)

            print(utente.monete_account)
            print(premio.costo_monete)
            if utente.monete_account >= premio.costo_monete:
                utente.monete_account -= premio.costo_monete
                utente.save()

                
                acquisto = AcquistoPremio.objects.create(
                    utente=utente,
                    premio=premio,
                    data_acquisto=timezone.now()
                )

                # Rispondi con successo e nuovo saldo
                return JsonResponse({
                    'success': True,
                    'new_coin_balance': utente.monete_account
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Insufficient coins.'
                })

        except Premio.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Item not found.'
            })

    return JsonResponse({
        'success': False,
        'error': 'Invalid request method.'
    })
