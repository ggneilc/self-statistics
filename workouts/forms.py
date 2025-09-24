from django import forms
from .models import Lift, WorkoutType, Set


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
        fields = ['exercise_name']
        widgets = {
            'exercise_name': forms.TextInput(attrs={'class': 'input', 'placeholder': ' '}),
        }


class SetForm(forms.ModelForm):
    class Meta:
        model = Set
        fields = ['reps', 'weight', 'rir', 'rest']
        widgets = {
            'reps': forms.NumberInput(attrs={'class': 'input', 'placeholder': ' '}),
            'weight': forms.NumberInput(attrs={'class': 'input', 'placeholder': ' '}),
            'rir': forms.NumberInput(attrs={'class': 'input', 'placeholder': ' '}),
            'rest': forms.NumberInput(attrs={'class': 'input', 'placeholder': ' '}),
        }
