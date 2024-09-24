# services.py
from .models import Faq

class FaqService:
    def get_all_faq():
      return Faq.objects.all()
   
