from django.shortcuts import render, redirect
from .forms import NuovaTransazioneForm
from django.http import JsonResponse
from django.views import View
from .forms import NuovaTransazioneForm

def nuova_transazione_view(request):
    if request.method == 'POST':
        form = NuovaTransazioneForm(request.POST, utente=request.user)
        if form.is_valid():
            form.save()
            return redirect('success_view')  
    else:
        form = NuovaTransazioneForm(utente=request.user)
    
    return render(request, 'personal/personalHomePage.html', {'form': form})


