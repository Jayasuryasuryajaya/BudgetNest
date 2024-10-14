
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
    path('cambia_obbiettivo_obbiettivoSpesa/<int:id>/<str:new_obbiettivo>/', cambia_obbiettivo_obbiettivoSpesa_view, name='cambia_obbiettivo_obbiettivoSpesa'),
    path('rinomina_data_scadenza_obbiettivoSpesa/<int:id>/<str:new_date>/',cambia_data_scadenza_obbiettivoSpesa_view, name= 'cambia_data_scadenza_obbiettivoSpesa'),
    path('elimina_obbiettivo/<int:id>/', elimina_obbiettivo_view, name='elimina_obbiettivo_spesa'),
    path('dashboard_family/', dashboard_family, name='dashboard_famiglia'),
    path('create_family/<str:nome_famiglia>/', crea_famiglia, name='crea_famiglia'),
    path('join_family/<str:codice>/', unisciti_famiglia, name='join_famiglia'),
    path('select_family/', family_switch, name='select_famiglia'),
    path('famiglia_selezionata/<int:id>/', accedi_famiglia, name='accesso_famiglia'),
    path('createAccountFam/<int:id>/', crea_account_famiglia, name='createAccountFamily'),
    path('createSavingsFam/<int:id>/', savings_section_famiglia, name='createSavingFamily'),
    path('createTransactionFamily/<int:famiglia>/', transaction_section_famiglia, name='createtransactionFamily'),
    path('createChallengeFamily/<int:famiglia>/', createFamChallenge, name='create_challenge'),
    path('elimina_challenge/<int:id>/', eliminaChallenge, name='elimina_challenge'),
    path('cambia_challenge/<int:id>/<str:new_date>/', modificaChallenge, name='cambia_data_scadenza_challenge'),
    path('investimentSection/', investments , name= "homePageInvestimenti"),
    path('api/stock/<str:symbol>/', get_stock_data, name='get_stock_data'),
    path('api/get-company-data/<str:company_name>/', get_company_data, name='search_company'),
    path('investimento/<str:symbol>/<str:nome_azienda>', investment_section, name = 'gestioneInvestimento'),
]




