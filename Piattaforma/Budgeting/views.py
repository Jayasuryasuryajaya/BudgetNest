from django.shortcuts import render, redirect
from .forms import NuovaTransazioneForm
from django.http import JsonResponse
from django.views import View
from .models import *
from .forms import NuovaTransazioneForm
from Users.services import *
from Budgeting.services import *

def nuova_transazione_view(request):
    if request.method == 'POST':
        form = NuovaTransazioneForm(request.POST, utente=request.user)
        if form.is_valid():
            form.save()
            return redirect('success_view')  
    else:
        form = NuovaTransazioneForm(utente=request.user)
    
    return render(request, 'personal/personalHomePage.html', {'form': form})

def create_custom_categories(request):
    utente = UserService.get_utenti_by_user(request.user.pk)
    sottocategorie = BudgetingService.get_sotto_categorie_utente(utente)
    context = {"utente" : utente, "sottocategorie" : sottocategorie}
    return render(request, 'custom_categories.html', context)

def update_subcategory(request, subcategory_id):
    subcategory = SottoCategoriaSpesa.objects.get(pk = subcategory_id)
    print(subcategory)
    new_name = request.POST.get('nome')
    print(new_name)
    if new_name:
        subcategory.nome = new_name
        subcategory.save()
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': subcategory.id,
                'nome': subcategory.nome,
            }
        })
    else:
        return JsonResponse({
            'status': 'error',
            'message': 'Nome non valido'
        }, status=400)
        
def delete_subcategory(request, subcategory_id):
    utente = UserService.get_utenti_by_user(request.user.pk)
    subcategory = SottoCategoriaSpesa.objects.get(pk = subcategory_id)
    print(subcategory)
    subcategory.delete()
    sottocategorie = BudgetingService.get_sotto_categorie_utente(utente=utente)
    sottocategorie_data = [
        {
            'id' : c.pk,
            'categoria_superiore' : c.categoria_superiore.nome,
            'nome' : c.nome,
            'data_creazione' : c.data_creazione.strftime('%Y-%m-%d'),  
        }
        for c in sottocategorie
        
    ]
    return JsonResponse({
            'success': True,
            'data': {
                'id': subcategory.id,
                'nome': subcategory.nome,
                'sotto_categorie' : sottocategorie_data
            }
        })
 