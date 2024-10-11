
from .models import *
from django.utils import timezone
from Users.services import *
from datetime import timedelta
from Accounts.services import *
class ChallengeService: 
    def get_family_challenge(famiglia):
        family_members = Utente.objects.filter(famiglia=famiglia)
        challenge_list = SfidaFamigliare.objects.filter(famiglia =famiglia)
        return list(challenge_list)
   
    def aggiorna_sfida(utente, categoria, nuovo_importo):
        sfide = SfidaFamigliare.objects.filter(
            categoria_target=categoria,
            sfidante=utente
        ).union(
            SfidaFamigliare.objects.filter(
                categoria_target=categoria,
                sfidato=utente
            )
        ) # Prendi solo la prima sfida trovata

        if sfide:
            for sfida_in_corso in sfide:
            # Aggiorna l'importo speso
                if utente == sfida_in_corso.sfidante:
                    sfida_in_corso.importo_sfidante -= nuovo_importo
                else:
                    sfida_in_corso.importo_sfidato -= nuovo_importo
                
                
                totale_importo = sfida_in_corso.importo_sfidante + sfida_in_corso.importo_sfidato
                
                if totale_importo > 0:
                    sfida_in_corso.percentuale_sfidante = (sfida_in_corso.importo_sfidante / totale_importo) * 100
                    sfida_in_corso.percentuale_sfidato = (sfida_in_corso.importo_sfidato / totale_importo) * 100
                
                # Salva le modifiche nel database
                sfida_in_corso.save()
                