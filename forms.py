from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import CustomUser, GroupSavings

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']  # Incluye username y email

    def clean(self):
        cleaned_data = super().clean()
        # Django ya valida las contraseñas con `password1` y `password2`
        # Así que no es necesario validar manualmente aquí
        return cleaned_data



class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email',
    }))
##############################################################################################3
class GroupSavingsForm(forms.ModelForm):
    class Meta:
        model = GroupSavings
        fields = ['name', 'goal_amount', 'weekly_minimum', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Group Name'}),
            'goal_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Goal Amount'}),
            'weekly_minimum': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Weekly Minimum'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Group Description'}),
        }

class ContributionForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount to contribute'}),
    )