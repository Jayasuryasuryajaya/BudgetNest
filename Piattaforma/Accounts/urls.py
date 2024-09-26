
from django.contrib import admin
from django.urls import path, include
from HomePage import urls as home_urls
from Users.views import *
from Accounts.views import *

urlpatterns = [
    path('',dashboard_utente , name='dashboard'),  
]



