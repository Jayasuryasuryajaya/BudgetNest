from django.forms import ModelForm
from Users.models import Utente
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import validate_email
from django.contrib.auth.models import User


class NuovoUtente(ModelForm):
    data_di_nascita = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'max': timezone.now().date().isoformat(),
                'class': 'form-control',
                'type': 'date',
            }
        )
    )
    
    class Meta:
        model = Utente
        fields = ["username", "email", "password", "nome", "cognome", "data_di_nascita", 
                  "indirizzo", "telefono", "sesso"]
        widgets = {
            'password': forms.PasswordInput(attrs={'placeholder': 'Choose a password (min. 8)', 'class': 'form-control'}), 
            'username': forms.TextInput(attrs={'placeholder': 'Choose a username',  'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email', 'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'placeholder': 'Enter your name' , 'class': 'form-control'}),
            'cognome': forms.TextInput(attrs={'placeholder': 'Enter your surname' , 'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'placeholder': 'Enter your phone number' , 'class': 'form-control'}),
            'indirizzo': forms.TextInput(attrs={'placeholder': 'Enter your address' , 'class': 'form-control'}),
            'sesso': forms.Select(attrs={'class': 'form-control'}),
            
                
          
        }

        
    def clean_username(self):
            username = self.cleaned_data.get("username")
            if User.objects.filter(username=username).exists():
                raise ValidationError("This username is already taken.")
            return username

    def clean_email(self):
                email = self.cleaned_data.get("email")
                try:
                    validate_email(email)
                except ValidationError:
                    raise ValidationError("Please enter a valid email address.")
            
                if User.objects.filter(email=email).exists():
                    raise ValidationError("This email is already in use.")
                return email

    def clean_password(self):
                password = self.cleaned_data.get("password")
                if len(password) < 8:
                    raise ValidationError("Password must be at least 8 characters long.")
                return password


    def clean_telefono(self):
                telefono = self.cleaned_data.get("telefono")
                if len(telefono) != 10 or not telefono.isdigit():
                    raise ValidationError("Phone number must be 10 digits long and only contain numbers.")
                return telefono
        
       
    
    
   