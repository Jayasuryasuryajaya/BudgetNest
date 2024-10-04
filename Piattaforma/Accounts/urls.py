
from django.contrib import admin
from django.urls import path, include
from HomePage import urls as home_urls
from Users.views import *
from Accounts.views import *
from Budgeting.views import *

urlpatterns = [
    path('',dashboard_utente , name='dashboard'),  
    path('personal/', personal_section, name = 'SezionePersonale'),
    path('transaction/', transaction_section, name = 'gestioneTransazione'),
    path('savings/', savings_section, name = 'gestionePianoRisparmio'),
    path('spending/', obbiettivoSpesa_section, name = 'gestioneObbiettivoSpesa'),
    path('elimina_transazione/<int:id>/', elimina_transazione, name='elimina_transazione'),
]



