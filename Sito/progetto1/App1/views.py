from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def welcome(request):
    return HttpResponse("ciao")

def welcome1(request):
    return HttpResponse("bella")

def welcome2(request):
    return HttpResponse("bella2")