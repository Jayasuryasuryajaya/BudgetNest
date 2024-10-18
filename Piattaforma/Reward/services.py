
from .models import *
from django.utils import timezone
from Users.services import *
from datetime import timedelta
from Accounts.services import *
import smtplib
from email.message import EmailMessage

class RewardService: 
    def assegna_premio(vincitore):
        vincitore.monete_account += 10
        vincitore.save()
    
    def get_premi():
        premi = Premio.objects.all()
        return premi

   
            
   