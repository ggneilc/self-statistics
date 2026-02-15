from django import forms
from .models import WorkoutType, Set, Movement


class WTypeForm(forms.ModelForm):
    class Meta:
        model = WorkoutType
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input', 'placeholder': ' '}),
            'color': forms.ColorInput(attrs={'class': 'color-input', 'placeholder': ' '}),
        }


class MovementForm(forms.ModelForm):
    class Meta:
        model = Movement
        fields = ['name', 'bodypart', 'secondary_bodypart', 'category']
        widgets = {
            'name':                 forms.TextInput(attrs={'class': 'input', 'placeholder': 'Exercise Name'}),
            'bodypart':             forms.Select(attrs={'class': 'input'}),
            'secondary_bodypart':   forms.Select(attrs={'class': 'input', 'style': 'font-size:x-small;'}),
            'category':             forms.Select(attrs={'class': 'input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Manually prepending a placeholder to the existing choices
        self.fields['bodypart'].choices = [('', 'Target Muscle')] + list(self.fields['bodypart'].choices)[1:]
        self.fields['secondary_bodypart'].choices = [('', 'Supporting Muscle (Optional)')] + list(self.fields['secondary_bodypart'].choices)[1:]
        self.fields['category'].choices = [('', 'Equipment')] + list(self.fields['category'].choices)[1:]


class SetForm(forms.ModelForm):
    class Meta:
        model = Set
        fields = ['reps', 'weight']
        widgets = {
            'reps': forms.NumberInput(attrs={'class': 'input', 'placeholder': 'Reps', 'style': 'flex: 3;'}),
            'weight': forms.NumberInput(attrs={'class': 'input', 'placeholder': 'Weight', 'style': 'flex: 3;'}),
        }
