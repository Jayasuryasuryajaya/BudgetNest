from django.shortcuts import render
from django.template import Template , Context
from Users.services import UserService  
from Budgeting.servicies import BudgetingService
from Faq.services import FaqService
# Create your views here.
def HomePage (request): 
    users = UserService.count_utenti
    families = UserService.count_famiglie
    transactions = BudgetingService.count_transazioni
    faqs = FaqService.get_all_faq
    context = {"utenti":users, "famiglie" : families, "transazioni": transactions, "faqs" : faqs}
    return render(request, "homepage/homepage.html", context)