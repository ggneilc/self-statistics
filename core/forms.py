
# forms.py

from django import forms
from .models import Profile


class ProfileForm(forms.ModelForm):
    height_ft = forms.IntegerField(label="Feet", min_value=0, required=False)
    height_in = forms.IntegerField(
        label="Inches", min_value=0, max_value=11, required=False)

    class Meta:
        model = Profile
        fields = ['timezone', 'gender', 'height_ft', 'height_in']
        widgets = {
            'timezone': forms.Select(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'height_ft': forms.NumberInput(
                attrs={'class': 'input', 'min_value': '0', 'max_value': '11'}
            ),
            'height_in': forms.NumberInput(
                attrs={'class': 'input', 'min_value': '0'}
            )
        }

    def clean(self):
        cleaned_data = super().clean()
        feet = cleaned_data.get("height_ft") or 0
        inches = cleaned_data.get("height_in") or 0

        total_cm = feet * 30.48 + inches * 2.54
        cleaned_data["height"] = total_cm
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.height = self.cleaned_data["height"]
        if commit:
            instance.save()
        return instance
