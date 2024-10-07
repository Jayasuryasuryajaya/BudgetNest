
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
    path('elimina_conto/<int:id>/', elimina_conto, name='elimina_conto'),
    path('rinomina_conto/<int:id>/<str:new_name>/',rename_conto, name= 'rinomina_conto'),
    path('rinomina_data_scadenza_piano/<int:id>/<str:new_date>/',cambia_data_scadenza_view, name= 'cambia_data_scadenza'),
    path('rinomina_obbiettivo_piano/<int:id>/<str:new_obbiettivo>/',cambia_obbiettivo_view, name= 'cambia_obbiettivo_piano'),
    path('elimina_piano/<int:id>/', elimina_piano_view, name='elimina_piano'),
    path('cambia_obbiettivo_obbiettivoSpesaa/<int:id>/<str:new_obbiettivo>/', cambia_obbiettivo_obbiettivoSpesa_view, name='cambia_obbiettivo_obbiettivoSpesa'),
    path('rinomina_data_scadenza_obbiettivoSpesa/<int:id>/<str:new_date>/',cambia_data_scadenza_obbiettivoSpesa_view, name= 'cambia_data_scadenza_obbiettivoSpesa'),
    path('elimina_obbiettivo/<int:id>/', elimina_obbiettivo_view, name='elimina_obbiettivo_spesa'),
]




