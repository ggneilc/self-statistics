from django import forms
from django.forms.models import inlineformset_factory
from .models import Meal, Food, MealConsumption, Ingredient, FoodUnit, Recipe


# 1. Define the base form for the Through Model
class MealConsumptionForm(forms.ModelForm):
    # Field to hold the Food's name (for display, not saved to DB)
    food_name = forms.CharField(max_length=255, required=False,
                                widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    # We only need the foreign key fields and the property field
    class Meta:
        model = MealConsumption
        # 'meal' will be set automatically by the formset
        fields = ['food', 'amount', 'unit',  'description',
                  'calories', 'protein', 'fat', 'carb', 'sugar', 'fiber', 'cholesterol',
                  'sodium', 'potassium', 'calcium', 'iron', 'magnesium', 'zinc',
                  'vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_b6', 'vitamin_b12', 'vitamin_e']
        widgets = {
            'food': forms.Select(attrs={'placeholder': 'Select food', 'class': 'tom-select-meal'}),
            'amount': forms.NumberInput(attrs={'placeholder': 'Amount', 'class': 'ingred-input'}),
            'unit': forms.Select(attrs={'class': 'unit-selector ingred-input'}),

            # manual
            'description': forms.TextInput(attrs={'placeholder': 'Description, i.e. \'French Fries\'', 'class': 'manual-desc-input'}),
            'calories': forms.NumberInput(attrs={'placeholder': 'Calories', 'class': 'manual-nut-input'}),
            'protein': forms.NumberInput(attrs={'placeholder': 'Protein', 'class': 'manual-nut-input'}),
            'fat': forms.NumberInput(attrs={'placeholder': 'Fat', 'class': 'manual-nut-input'}),
            'carb': forms.NumberInput(attrs={'placeholder': 'Carbs', 'class': 'manual-nut-input'}),
            'sugar': forms.NumberInput(attrs={'placeholder': 'Sugar', 'class': 'manual-nut-input'}),
            'fiber': forms.NumberInput(attrs={'placeholder': 'Fiber', 'class': 'manual-nut-input'}),
            'cholesterol': forms.NumberInput(attrs={'placeholder': 'Cholesterol', 'class': 'manual-nut-input'}),
            'sodium': forms.NumberInput(attrs={'placeholder': 'Sodium', 'class': 'manual-nut-input'}),
            'potassium': forms.NumberInput(attrs={'placeholder': 'Potassium', 'class': 'manual-nut-input'}),
            'calcium': forms.NumberInput(attrs={'placeholder': 'Calcium', 'class': 'manual-nut-input'}),
            'iron': forms.NumberInput(attrs={'placeholder': 'Iron', 'class': 'manual-nut-input'}),
            'magnesium': forms.NumberInput(attrs={'placeholder': 'Magnesium', 'class': 'manual-nut-input'}),
            'zinc': forms.NumberInput(attrs={'placeholder': 'Zinc', 'class': 'manual-nut-input'}),
            'vitamin_a': forms.NumberInput(attrs={'placeholder': 'A', 'class': 'manual-nut-input'}),
            'vitamin_b6': forms.NumberInput(attrs={'placeholder': 'B6', 'class': 'manual-nut-input'}),
            'vitamin_b12': forms.NumberInput(attrs={'placeholder': 'B12', 'class': 'manual-nut-input'}),
            'vitamin_c': forms.NumberInput(attrs={'placeholder': 'C', 'class': 'manual-nut-input'}),
            'vitamin_d': forms.NumberInput(attrs={'placeholder': 'D', 'class': 'manual-nut-input'}),
            'vitamin_e': forms.NumberInput(attrs={'placeholder': 'E', 'class': 'manual-nut-input'}),
        }


    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) # Grab the user from kwargs
        super().__init__(*args, **kwargs)
        qs = Food.objects.filter(is_active=True)
        if user:
            qs = qs.filter(owner=user)
        self.fields['food'].queryset = qs.distinct()
        self.fields['unit'].choices = [('', 'Unit')]

        # make all fields not required: view will filter based on type of entry
        for field in self.fields.values():
            field.required = False

    def clean(self):
        cleaned_data = super().clean()
        food = cleaned_data.get('food')
        amount = cleaned_data.get('amount')
        unit = cleaned_data.get('unit')
        description = cleaned_data.get('description')

        # Case A: User tried to log a Database Food
        if food:
            if amount is None or unit is None:
                raise forms.ValidationError(
                    "If you select a food, you must also provide an amount and a unit."
                )
        
        # Case B: User tried to log a Manual Entry
        elif description:
            # We allow nutrients to be 0/blank, so no extra check needed here
            pass

        # Case C: User entered an amount/unit but forgot the Food
        elif amount is not None or unit is not None:
             raise forms.ValidationError(
                "You entered an amount/unit but didn't select a food. "
                "Did you mean to use a Manual Entry description?"
            )

        # Case D: Totally blank row
        # Django's formset ignores totally empty 'extra' forms automatically, 
        # so we don't need to raise an error here.
        
        return cleaned_data


class MealForm(forms.ModelForm):
    class Meta:
        model = Meal
        fields = ['name']

        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Lunch, Hot Dog, etc...', 'class': 'meal-name-input'}),
        }


# 1. Define the base form for the IngredientComposition Through Model
class IngredientForm(forms.ModelForm):
    # Similar display field for ingredient name
    ingredient_name = forms.CharField(max_length=255, required=False,
                                      widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    class Meta:
        model = Ingredient
        fields = ['ingredient', 'amount', 'unit']
        widgets = {
            'ingredient': forms.Select(attrs={'placeholder': 'ingredient', 'class': 'tom-select-ingredient'}),
            'amount': forms.NumberInput(attrs={'placeholder': 'Amount', 'class': 'ingred-input'}),
            'unit': forms.Select(attrs={'class': 'unit-selector ingred-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) # Grab the user from kwargs
        super().__init__(*args, **kwargs)
        qs = Food.objects.filter(is_active=True)
        if user:
            qs = qs.filter(owner=user)
        self.fields['ingredient'].queryset = qs.distinct()
        self.fields['unit'].choices = [('', 'Unit')]


class FoodForm(forms.ModelForm):
    class Meta:
        model = Food
        # Only fields the user sets for a custom food
        fields = ['name']


class FoodUnitForm(forms.ModelForm):
    class Meta:
        model = FoodUnit
        fields = ['name', 'gram_weight', 'is_standard']


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['food', 'instructions', 'prep_time', 'cook_time']
        widgets = {
            'food': forms.Select(attrs={'class': 'tom-select-recipe-food'}),
            'instructions': forms.Textarea(attrs={
                'rows': 10, 
                'placeholder': '1. Dice the onions...\n2. Sauté until translucent...',
                'style': 'resize: vertical;' # Allows user to pull the corner down
            }),
            'prep_time': forms.NumberInput(attrs={'placeholder': 'Mins'}),
            'cook_time': forms.NumberInput(attrs={'placeholder': 'Mins'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) # Grab the user from kwargs
        super().__init__(*args, **kwargs)
        qs = Food.objects.filter(ingredient__isnull=False)
        if user:
            qs = qs.filter(owner=user)
        self.fields['food'].queryset = qs.distinct()