from django.forms import ModelForm
from Accounts.models import Conto, TipoConto
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from Users.services import *
from django import forms
from .models import Transazione, CategoriaSpesa, SottoCategoriaSpesa, Conto, PianoDiRisparmio, ObbiettivoSpesa, TipoRinnovo
from Accounts.services import *
from Users.services import *
from django.db.models import Q
from datetime import timedelta
from Budgeting.services import *


class NuovaTransazioneForm(forms.ModelForm):
    class Meta:
        model = Transazione
        fields = [
            'importo',
            'data',
            'tipo_transazione',
            'conto',
            'categoria',
            'sotto_categoria',
            'descrizione',
            'tipo_rinnovo',
            'numero_azioni',
            'prezzo_azione',
            'borsa',
            'valuta',
            'ticker',
            'conto_arrivo'
        ]
        widgets = {
            'importo': forms.NumberInput(attrs={
                'placeholder': 'Enter amount',
                'class': 'form-control',
                'step': '0.01',
            }),
            'data': forms.DateInput(attrs={
                'placeholder': 'Select date',
                'class': 'form-control',
                'type': 'date',
            }),
            'descrizione': forms.Textarea(attrs={
                'placeholder': 'Enter description',
                'class': 'form-control',
                'rows': 3,
            }),
            'tipo_transazione': forms.Select(attrs={'class': 'form-control'}),
            'conto': forms.Select(attrs={'class': 'form-control'}),
            'conto_arrivo': forms.Select(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'sotto_categoria': forms.Select(attrs={'class': 'form-control'}),
            'tipo_rinnovo': forms.Select(attrs={'class': 'form-control'}),
            'numero_azioni': forms.NumberInput(attrs={
                'placeholder': 'Enter number of shares',
                'class': 'form-control',
                'step': '1',
                'min': '0',
            }),
            'prezzo_azione': forms.NumberInput(attrs={
                'placeholder': 'Enter share price',
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
            }),
            'borsa': forms.TextInput(attrs={
                'placeholder': 'Enter stock exchange',
                'class': 'form-control',
            }),
            'valuta': forms.TextInput(attrs={
                'placeholder': 'Enter currency (e.g., USD)',
                'class': 'form-control',
                'maxlength': 3,
            }),
            'ticker': forms.TextInput(attrs={
                'placeholder': 'Enter the ticker (e.g., VUSA)',
                'class': 'form-control',
                
            }),
        }
  
    
    def __init__(self, *args, utente=None, **kwargs):  
        super().__init__(*args, **kwargs)  
    
        
        Utente = UserService.get_utenti_by_user(utente.id)

        self.fields['conto'].choices = [(conto.pk, str(conto)) for conto in AccountService.get_conti_utente(Utente.pk)]
        self.fields['conto'].empty_label = "Select account"

        self.fields['conto_arrivo'].choices = [(conto.pk, str(conto)) for conto in AccountService.get_conti_utente(Utente.pk)]
        self.fields['conto_arrivo'].empty_label = "Select arriving account"
        
        self.fields['categoria'].queryset = CategoriaSpesa.objects.all()
        self.fields['categoria'].empty_label = "Select category"

        # Imposta il queryset per 'sotto_categoria' usando l'utente
        self.fields['sotto_categoria'].queryset = SottoCategoriaSpesa.objects.filter(Q(utente=Utente.pk) | Q(personalizzata=False))
        self.fields['sotto_categoria'].empty_label = "Select sub-category"
        
        
        
   
    def clean(self):
        cleaned_data = super().clean()
        tipo_transazione = cleaned_data.get('tipo_transazione')
        conto = cleaned_data.get('conto')
        importo = cleaned_data.get('importo')
        data = cleaned_data.get('data')
        categoria = cleaned_data.get('categoria')
        sotto_categoria = cleaned_data.get('sotto_categoria')
        
        tipo_rinnovo = cleaned_data.get('tipo_rinnovo')
        
        # 1. If the transaction type is not investment, do not allow operations on an investment account
        if tipo_transazione and conto:
            conto_obj = Conto.objects.get(pk=conto.pk)
            if (tipo_transazione != 'investimento' and tipo_transazione != 'trasferimento') and conto_obj.tipo == 'investimento':
                raise ValidationError("You cannot perform operations on an investment account unless the transaction type is investment or transfer .")

        # 2. Ensure the selected sub-category corresponds to the chosen category
        if categoria and sotto_categoria:
            sottocategoria_obj = SottoCategoriaSpesa.objects.get(pk=sotto_categoria.pk)
           
            if sottocategoria_obj.categoria_superiore.pk != categoria.pk:
                raise ValidationError("The selected sub-category does not correspond to the chosen category.")

        # 3. The transaction amount cannot exceed the selected account balance, unless it's a future transaction
        if importo and conto:
            conto_obj = Conto.objects.get(pk=conto.pk)
            if (-importo) > conto_obj.saldo:
                raise ValidationError("The amount cannot exceed the selected account balance.")

        
        if data and data > timezone.now().date() and tipo_transazione != "futura" and tipo_transazione != "periodica":
            raise ValidationError("The selected date cannot be in the future (you should use a future transaction)")

        if tipo_transazione == "futura" and data <= timezone.now().date() :
            raise ValidationError("Future transactions cannot have today's date or less")

        if tipo_transazione == "periodica" and data <= (timezone.now().date() - timedelta(days=7)):
            raise ValidationError("The initial date for periodic transactions cannot be older than one week.")

        if cleaned_data.get('conto') == cleaned_data.get('conto_arrivo') and tipo_transazione == "trasferimento":
            raise ValidationError("The selected accounts cannot be the same.")

        if tipo_transazione == 'periodica' and not tipo_rinnovo:
         raise ValidationError("A periodic transaction must have a renewal type.")
        
        if cleaned_data.get('importo') <= 0 and tipo_transazione == "trasferimento":
            raise ValidationError("The amount must be positive")
        
        if tipo_transazione == "trasferimento" and importo <= 0:
            raise ValidationError("The transfer amount must be positive.")
        
        return cleaned_data


class NuovaTransazioneFamigliaForm(forms.ModelForm):
    class Meta:
        model = Transazione
        fields = [
            'importo',
            'data',
            'tipo_transazione',
            'conto',
            'categoria',
            'sotto_categoria',
            'descrizione',
            'tipo_rinnovo',
            'numero_azioni',
            'prezzo_azione',
            'borsa',
            'valuta',
            'ticker',
            'conto_arrivo'
        ]
        widgets = {
            'importo': forms.NumberInput(attrs={
                'placeholder': 'Enter amount',
                'class': 'form-control',
                'step': '0.01',
            }),
            'data': forms.DateInput(attrs={
                'placeholder': 'Select date',
                'class': 'form-control',
                'type': 'date',
            }),
            'descrizione': forms.Textarea(attrs={
                'placeholder': 'Enter description',
                'class': 'form-control',
                'rows': 3,
            }),
            'tipo_transazione': forms.Select(attrs={'class': 'form-control'}),
            'conto': forms.Select(attrs={'class': 'form-control'}),
            'conto_arrivo': forms.Select(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'sotto_categoria': forms.Select(attrs={'class': 'form-control'}),
            'tipo_rinnovo': forms.Select(attrs={'class': 'form-control'}),
            'numero_azioni': forms.NumberInput(attrs={
                'placeholder': 'Enter number of shares',
                'class': 'form-control',
                'step': '1',
                'min': '0',
            }),
            'prezzo_azione': forms.NumberInput(attrs={
                'placeholder': 'Enter share price',
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
            }),
            'borsa': forms.TextInput(attrs={
                'placeholder': 'Enter stock exchange',
                'class': 'form-control',
            }),
            'valuta': forms.TextInput(attrs={
                'placeholder': 'Enter currency (e.g., USD)',
                'class': 'form-control',
                'maxlength': 3,
            }),
            'ticker': forms.TextInput(attrs={
                'placeholder': 'Enter the ticker (e.g., VUSA)',
                'class': 'form-control',
                
            }),
        }
  
    
    def __init__(self, *args, utente=None, famiglia = None, **kwargs):  
        super().__init__(*args, **kwargs)  
    
        
        Utente = UserService.get_utenti_by_user(utente.id)

        self.fields['conto'].choices = [(conto.pk, str(conto)) for conto in AccountService.get_family_accounts(famiglia)]
        self.fields['conto'].empty_label = "Select account"

        self.fields['conto_arrivo'].choices = [(conto.pk, str(conto)) for conto in AccountService.get_family_accounts(famiglia)]
        self.fields['conto_arrivo'].empty_label = "Select arriving account"
        
        self.fields['categoria'].queryset = CategoriaSpesa.objects.all()
        self.fields['categoria'].empty_label = "Select category"

       
        self.fields['sotto_categoria'].queryset = SottoCategoriaSpesa.objects.filter(Q(utente=Utente.pk) | Q(personalizzata=False))
        self.fields['sotto_categoria'].empty_label = "Select sub-category"
        
        
        
   
    def clean(self):
        cleaned_data = super().clean()
        tipo_transazione = cleaned_data.get('tipo_transazione')
        conto = cleaned_data.get('conto')
        importo = cleaned_data.get('importo')
        data = cleaned_data.get('data')
        categoria = cleaned_data.get('categoria')
        sotto_categoria = cleaned_data.get('sotto_categoria')
        
        tipo_rinnovo = cleaned_data.get('tipo_rinnovo')
        
        # 1. If the transaction type is not investment, do not allow operations on an investment account
        if tipo_transazione and conto:
            conto_obj = Conto.objects.get(pk=conto.pk)
            if (tipo_transazione != 'investimento' and tipo_transazione != 'trasferimento') and conto_obj.tipo == 'investimento':
                raise ValidationError("You cannot perform operations on an investment account unless the transaction type is investment or transfer .")

        # 2. Ensure the selected sub-category corresponds to the chosen category
        if categoria and sotto_categoria:
            sottocategoria_obj = SottoCategoriaSpesa.objects.get(pk=sotto_categoria.pk)
           
            if sottocategoria_obj.categoria_superiore.pk != categoria.pk:
                raise ValidationError("The selected sub-category does not correspond to the chosen category.")

        # 3. The transaction amount cannot exceed the selected account balance, unless it's a future transaction
        if importo and conto:
            conto_obj = Conto.objects.get(pk=conto.pk)
            if (-importo) > conto_obj.saldo:
                raise ValidationError("The amount cannot exceed the selected account balance.")

        
        if data and data > timezone.now().date() and tipo_transazione != "futura" and tipo_transazione != "periodica":
            raise ValidationError("The selected date cannot be in the future (you should use a future transaction)")

        if tipo_transazione == "futura" and data <= timezone.now().date() :
            raise ValidationError("Future transactions cannot have today's date or less")

        if tipo_transazione == "periodica" and data <= (timezone.now().date() - timedelta(days=7)):
            raise ValidationError("The initial date for periodic transactions cannot be older than one week.")

        if cleaned_data.get('conto') == cleaned_data.get('conto_arrivo') and tipo_transazione == "trasferimento":
            raise ValidationError("The selected accounts cannot be the same.")

        if tipo_transazione == 'periodica' and not tipo_rinnovo:
         raise ValidationError("A periodic transaction must have a renewal type.")
        
        if cleaned_data.get('importo') <= 0 and tipo_transazione == "trasferimento":
            raise ValidationError("The amount must be positive")
        
        if tipo_transazione == "trasferimento" and importo <= 0:
            raise ValidationError("The transfer amount must be positive.")
        
        return cleaned_data


class NuovoPianoRisparmo(forms.ModelForm):
    class Meta:
        model = PianoDiRisparmio
        fields = [
            'obbiettivo',
            'data_scadenza',
            'conto',
        ]
        widgets = {
            'obbiettivo': forms.NumberInput(attrs={
                'placeholder': 'Enter amount',
                'class': 'form-control',
                'step': '0.01',
            }),
            'data_scadenza': forms.DateInput(attrs={
                'placeholder': 'Select date',
                'class': 'form-control',
                'type': 'date',
            }),
            'conto': forms.Select(attrs={'class': 'form-control'}),
            
        }
  
    
    def __init__(self, *args, utente=None, **kwargs):  
        super().__init__(*args, **kwargs)  
    
        # Controlla se l'utente è fornito
        if utente is not None:
            utente_obj = UserService.get_utenti_by_user(utente.id)

            tipo_conto_desiderato = 'risparmio'  # Specifica il tipo di conto che vuoi filtrare
            conti_filtrati = [
                conto for conto in AccountService.get_conti_utente(utente_obj.pk) 
                if conto.tipo == tipo_conto_desiderato
            ]

            # Imposta le choices filtrate
            self.fields['conto'].choices = [(conto.pk, str(conto)) for conto in conti_filtrati]
            self.fields['conto'].empty_label = "Select account"
        
        # Puoi usar

   
    def clean(self):
        cleaned_data = super().clean()

        obbiettivo = cleaned_data.get('obbiettivo')
        data_scadenza = cleaned_data.get('data_scadenza')
        
        
        if(obbiettivo <= 0):
             raise ValidationError("The amount must be positive")
        
        if data_scadenza and data_scadenza <= (timezone.now().date()  + timedelta(days=7)):
            raise ValidationError("The due date must be at least one week from today")
        return cleaned_data
    

class NuovoPianoRisparmoFamiglia(forms.ModelForm):
    class Meta:
        model = PianoDiRisparmio
        fields = [
            'obbiettivo',
            'data_scadenza',
            'conto',
        ]
        widgets = {
            'obbiettivo': forms.NumberInput(attrs={
                'placeholder': 'Enter amount',
                'class': 'form-control',
                'step': '0.01',
            }),
            'data_scadenza': forms.DateInput(attrs={
                'placeholder': 'Select date',
                'class': 'form-control',
                'type': 'date',
            }),
            'conto': forms.Select(attrs={'class': 'form-control'}),
            
        }
  
    
    def __init__(self, *args, famiglia = None, **kwargs):  
        super().__init__(*args, **kwargs)  
    
       
        conti_filtrati = AccountService.get_family_accounts(famiglia) 
               

        self.fields['conto'].choices = [(conto.pk, str(conto)) for conto in conti_filtrati]
        self.fields['conto'].empty_label = "Select account"
        
      

   
    def clean(self):
        cleaned_data = super().clean()

        obbiettivo = cleaned_data.get('obbiettivo')
        data_scadenza = cleaned_data.get('data_scadenza')
        
        
        if(obbiettivo <= 0):
             raise ValidationError("The amount must be positive")
        
        if data_scadenza and data_scadenza <= (timezone.now().date()  + timedelta(days=7)):
            raise ValidationError("The due date must be at least one week from today")
        return cleaned_data
    


class ObbiettivoSpesaForm(forms.ModelForm):
    class Meta:
        model = ObbiettivoSpesa
        fields = ['importo', 'categoria_target', 'tipo']
        widgets = {
            'importo': forms.NumberInput(attrs={
                'placeholder': 'Enter amount',
                'class': 'form-control',
                'step': '0.01',
            }),
            'categoria_target': forms.Select(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, utente=None, **kwargs):  
            super().__init__(*args, **kwargs)  
            self.fields['categoria_target'].choices = [(categoria.pk, str(categoria)) for categoria in BudgetingService.get_categorie_utente()]
            self.fields['tipo'].choices = ObbiettivoSpesa.TIPO_SCELTE

    def clean(self):
        cleaned_data = super().clean()
        obbiettivo = cleaned_data.get('importo')
        if(obbiettivo <= 0):
             raise ValidationError("The amount must be positive")
        
