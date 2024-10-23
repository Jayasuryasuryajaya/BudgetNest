from django.shortcuts import render, redirect
from .forms import NuovaTransazioneForm, Sotto_Categoria_Form
from django.http import JsonResponse
from django.views import View
from .models import *
from .forms import NuovaTransazioneForm
from Users.services import *
from Budgeting.services import *
from django.contrib.auth.decorators import login_required

@login_required
def nuova_transazione_view(request):
    if request.method == 'POST':
        form = NuovaTransazioneForm(request.POST, utente=request.user)
        if form.is_valid():
            form.save()
            return redirect('success_view')  
    else:
        form = NuovaTransazioneForm(utente=request.user)
    
    return render(request, 'personal/personalHomePage.html', {'form': form})

@login_required
def create_custom_categories(request):
    utente = UserService.get_utenti_by_user(request.user.pk)
    form = Sotto_Categoria_Form()
    sottocategorie = BudgetingService.get_sotto_categorie_utente(utente)
    context = {"utente" : utente, "sottocategorie" : sottocategorie, "form" : form}
    return render(request, 'custom_categories.html', context)

@login_required
def update_subcategory(request, subcategory_id):
    subcategory = SottoCategoriaSpesa.objects.get(pk = subcategory_id)
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
      
@login_required  
def delete_subcategory(request, subcategory_id):
    utente = UserService.get_utenti_by_user(request.user.pk)
    subcategory = SottoCategoriaSpesa.objects.get(pk = subcategory_id)
    print(subcategory)
    subcategory.delete()
    return JsonResponse({
            'success': True,
        })
 
@login_required
def create_sub(request):
    utente = UserService.get_utenti_by_user(request.user.pk)
    if request.method == 'POST':
        form = Sotto_Categoria_Form(request.POST)

        if form.is_valid(): 
            
            categoria_superiore = (form.cleaned_data['categoria_superiore'])
           
       
            SottoCategoriaSpesa.objects.create(
                nome=form.cleaned_data['nome'],
                categoria_superiore=categoria_superiore,  
                utente=utente,
                data_creazione=timezone.now().date(),
                personalizzata=True
            )
            
            
            sottocategorie = BudgetingService.get_sotto_categorie_utente(utente=utente)
            sottocategorie_data = [
                {
                    'id': c.pk,
                    'categoria_superiore': c.categoria_superiore.nome,
                    'nome': c.nome,
                    'data_creazione': c.data_creazione.strftime('%Y-%m-%d'),
                }
                for c in sottocategorie
            ]
            
            return JsonResponse({'success': True, 'sottocategorie': sottocategorie_data})
        else:
            
            print("Errori di validazione:", form.errors) 
            return JsonResponse({'success': False, 'errors': form.errors})

    return JsonResponse({'success': False, 'message': 'Invalid request'})
