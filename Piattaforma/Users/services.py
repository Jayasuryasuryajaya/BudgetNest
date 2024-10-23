
from .models import Utente,Famiglia  

class UserService:
    def get_all_utente():
      return Utente.objects.all()
    
    def get_all_Famiglia():
      return Famiglia.objects.all()
       
    def count_utenti():
        return Utente.objects.count()  
    
    def count_famiglie():
        return Famiglia.objects.count()
      
    def get_utenti_by_user(id):
        return Utente.objects.get(user_profile_id = id)  
