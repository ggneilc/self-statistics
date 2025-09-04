from django import forms
from .models import Lift, WorkoutType

class WTypeForm(forms.ModelForm):
    class Meta:
        model = WorkoutType
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input', 'placeholder': ' '}),
            'color': forms.TextInput(attrs={'class': 'input', 'placeholder': ' '}),
        }


class LiftForm(forms.ModelForm):
    class Meta:
        model = Lift
        fields = ['name', 'sets', 'reps', 'weight']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input', 'placeholder': ' '}),
            'sets': forms.NumberInput(attrs={'class': 'input', 'placeholder': ' '}),
            'reps': forms.NumberInput(attrs={'class': 'input', 'placeholder': ' '}),
            'weight': forms.NumberInput(attrs={'class': 'input', 'placeholder': ' '}),
        }
