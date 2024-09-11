from django.urls import path
from App1.views import *

urlpatterns = [
    path("",welcome,name = "prima rotta"),
    path("App1/view-b", welcome1, name = "seconda rotta"),
    path("App1/view-c", welcome2, name= "terza rotta"),
    
    
]