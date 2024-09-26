from django.shortcuts import render, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from .forms import NuovoUtente 
from .forms import *
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

@never_cache
def Login(request):
    form = AuthenticationForm(request, data=request.POST or None)
    
    print("Dati ricevuti:", request.POST) 
    print("prova")
    if form.is_valid():
        user = form.get_user()
        auth_login(request, user)
        print("funziona")
        
        
    return render(request, 'registration/login.html', {'form': form})


@never_cache
def logout_view(request):
    logout(request)
    return redirect('HomePageUrls')


@never_cache
def registration(request):
    if request.method == "POST":
        form = NuovoUtente(request.POST)
        if form.is_valid(): 
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            
            user = User.objects.create_user(username=username, email=email, password=password)
            Utente.objects.create(
                user_profile=user,
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],  # Usa un hash per la password
                nome=form.cleaned_data['nome'],
                cognome=form.cleaned_data['cognome'],
                data_di_nascita=form.cleaned_data['data_di_nascita'],
                indirizzo=form.cleaned_data.get('indirizzo', ''),
                telefono=form.cleaned_data['telefono'],
                sesso=form.cleaned_data['sesso'],
                monete_account=0,
                famiglia= None,
                data_registrazione=timezone.now()
            )
           
            utente_loggato = authenticate(request, username=username, password=password)
            if utente_loggato is not None:
                auth_login(request, utente_loggato)
            return redirect('dashboard')
    
        
    else:
        form = NuovoUtente()
    
    context = {"form": form}
    return render(request, 'getstarted/registration.html', context)


