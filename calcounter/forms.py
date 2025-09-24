from django import forms
from .models import Food


class FoodForm(forms.ModelForm):
    class Meta:
        model = Food
        fields = ['name', 'calories', 'protein', 'fat', 'carb']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input', 'placeholder': ' '}),
            'calories': forms.NumberInput(attrs={'class': 'input', 'placeholder': ' '}),
            'protein': forms.NumberInput(attrs={'class': 'input', 'placeholder': ' '}),
            'fat': forms.NumberInput(attrs={'class': 'input', 'placeholder': ' '}),
            'carb': forms.NumberInput(attrs={'class': 'input', 'placeholder': ' '}),
        }
