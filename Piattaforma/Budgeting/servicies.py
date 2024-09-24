
from .models import Transazione

class BudgetingService: 
    def count_transazioni():
        return Transazione.objects.count()  
    
   