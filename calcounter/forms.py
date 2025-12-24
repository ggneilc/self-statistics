from django import forms
from django.forms.models import inlineformset_factory
from .models import Meal, Food, MealConsumption, Ingredient


# 1. Define the base form for the Through Model
class MealConsumptionForm(forms.ModelForm):
    # Field to hold the Food's name (for display, not saved to DB)
    food_name = forms.CharField(max_length=255, required=False,
                                widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    # We only need the foreign key fields and the property field
    class Meta:
        model = MealConsumption
        # 'meal' will be set automatically by the formset
        fields = ['food', 'serving_g']
        widgets = {
            'food': forms.HiddenInput(),
            'serving_g': forms.NumberInput(attrs={'placeholder': 'Serving size (grams)'})
        }


# 2. Define the Formset for Meal Consumption
# This is the "factory" that handles the dynamic list of rows
MealConsumptionFormSet = inlineformset_factory(
    parent_model=Meal,
    model=MealConsumption,
    form=MealConsumptionForm,
    extra=1,  # Start with one empty form row
    can_delete=True  # Allow users to remove rows
)


class MealForm(forms.ModelForm):
    class Meta:
        model = Meal
        fields = ['name', 'day', 'is_template']


# 1. Define the base form for the IngredientComposition Through Model
class IngredientForm(forms.ModelForm):
    # Similar display field for ingredient name
    ingredient_name = forms.CharField(max_length=255, required=False,
                                      widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    class Meta:
        model = Ingredient
        fields = ['ingredient', 'quantity_g']
        widgets = {
            'ingredient': forms.HiddenInput(),
            'quantity_g': forms.NumberInput(attrs={'placeholder': 'Quantity (grams)'})
        }


# 2. Define the Formset for Ingredient Composition
IngredientFormSet = inlineformset_factory(
    parent_model=Food,  # Parent is the complex Food being created
    model=Ingredient,
    form=IngredientForm,
    extra=1,
    can_delete=True,
    fk_name="complex_food"
)


class FoodForm(forms.ModelForm):
    class Meta:
        model = Food
        # Only fields the user sets for a custom food
        fields = ['name']
