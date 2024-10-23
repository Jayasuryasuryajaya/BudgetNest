
from .models import *
from django.utils import timezone
from Users.services import *
from datetime import datetime, timedelta
from Accounts.services import *
from Reward.services import *
class ChallengeService: 
    def get_family_challenge(famiglia):
        challenge_list = SfidaFamigliare.objects.filter(famiglia =famiglia, data_scadenza__gte=timezone.now().date() )
        return list(challenge_list)
   
    def aggiorna_sfida(utente, categoria, nuovo_importo, data_transazione):
        data  = datetime.strptime(data_transazione, '%Y-%m-%d').date()
        sfide = SfidaFamigliare.objects.filter(
            categoria_target=categoria,
            sfidante=utente,
            data_creazione__lte=data, 
            data_scadenza__gte=data   
        ).union(
            SfidaFamigliare.objects.filter(
                categoria_target=categoria,
                sfidato=utente,
                data_creazione__lte=data,  
                data_scadenza__gte=data   
            )
        ) 

        if sfide:
            for sfida_in_corso in sfide:
        
                if utente == sfida_in_corso.sfidante:
                    sfida_in_corso.importo_sfidante -= nuovo_importo
                else:
                    sfida_in_corso.importo_sfidato -= nuovo_importo
                
                
                totale_importo = sfida_in_corso.importo_sfidante + sfida_in_corso.importo_sfidato
                
                if totale_importo > 0:
                    sfida_in_corso.percentuale_sfidante = (sfida_in_corso.importo_sfidante / totale_importo) * 100
                    sfida_in_corso.percentuale_sfidato = (sfida_in_corso.importo_sfidato / totale_importo) * 100
                
                
                sfida_in_corso.save()
          
    def concludi_sfida(utente):
        sfide = SfidaFamigliare.objects.filter(
            sfidante=utente
        ).union(
            SfidaFamigliare.objects.filter(
                sfidato=utente
            )
        ) 
        if sfide:
            for sfida_in_corso in sfide:
                if sfida_in_corso.data_scadenza < timezone.now().date() and  sfida_in_corso.conclusa != True:
                    sfida_in_corso.conclusa = True
                    if(sfida_in_corso.importo_sfidante > sfida_in_corso.importo_sfidato):
                        sfida_in_corso.vincitore = sfida_in_corso.sfidato
                    if (sfida_in_corso.importo_sfidante == sfida_in_corso.importo_sfidato):
                        sfida_in_corso.vincitore = None
                    if(sfida_in_corso.importo_sfidante < sfida_in_corso.importo_sfidato):
                        sfida_in_corso.vincitore = sfida_in_corso.sfidante
                    sfida_in_corso.save() 
                    print(sfida_in_corso.vincitore)
                    RewardService.assegna_premio(sfida_in_corso.vincitore)
                    
    
    

