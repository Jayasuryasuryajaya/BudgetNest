from django.forms import ModelForm
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from Accounts.services import AccountService
from Budgeting.models import CategoriaSpesa
from .models import SfidaFamigliare
from Users.services import UserService

class NuovaSfidaFamigliare(ModelForm):

    data_scadenza = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )
   
    descrizione = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Enter challenge description',
            'class': 'form-control',
            'rows': 4,
        })
    )

    class Meta:
        model = SfidaFamigliare
        fields = [
            'sfidato', 
            'data_scadenza', 'descrizione', 'categoria_target'
        ]
        widgets = {
            'sfidato': forms.Select(attrs={'class': 'form-control'}),
            'categoria_target': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args,famiglia = None, utente = None, **kwargs):
        self.request = kwargs.pop('request', None) 
        super(NuovaSfidaFamigliare, self).__init__(*args, **kwargs)

        family_members = [persona for persona in AccountService.get_family_members(famiglia) if persona.pk != utente.pk]

        self.fields['sfidato'].choices = [(persona.pk, str(persona)) for persona in family_members]
        self.fields['sfidato'].empty_label = "Select challenger"
        
        self.fields['categoria_target'].queryset = CategoriaSpesa.objects.all()
        self.fields['categoria_target'].empty_label = "Select category"
        
    def clean_data_scadenza(self):
        data_scadenza = self.cleaned_data.get("data_scadenza")
        if data_scadenza < timezone.now().date():
            raise ValidationError("The expiration date cannot be in the past.")
        return data_scadenza
