"""
    Calcounter manages Food
"""
from django.shortcuts import get_object_or_404, render, HttpResponse
from django.db.models import Sum
from .models import Food, Meal, Ingredient, MealConsumption, PantryItem, FoodUnit, Recipe
from .forms import FoodForm, FoodUnitForm, MealForm, IngredientForm, MealConsumptionForm, RecipeForm
from core.utils import get_or_create_day
from core.models import RDA_LOOKUP
from django.forms.models import inlineformset_factory

from copy import copy
from datetime import datetime, date
import requests
import os

USDA_KEY = os.getenv('USDA_API_KEY')

NUTRIENT_MAP = {
    # Macros
    "Energy":        208,   # calories
    "Protein":       203,
    "Fat":           204,
    "Carbohydrates": 205,
    "Sugar":         269,
    "Fiber":         291,
    "Cholesterol":   601,
    # Minerals
    "Calcium":      301,
    "Iron":         303,
    "Magnesium":    304,
    "Potassium":    306,
    "Sodium":       307,
    "Zinc":         309,
    # Vitamins (A-E Complex)
    "Vitamin A":    320,
    "Vitamin B-6":  415,
    "Vitamin B-12": 418,
    "Vitamin C":    401,
    "Vitamin D":    328,
    "Vitamin E":    323,
    # Alcohol: 221
    # Caffiene: 262
}
MACRO = [208, 203, 204, 205, 269, 291, 601]
MINERAL = [301, 303, 304, 306, 307, 309]
VITAMIN = [320, 415, 418, 401, 328, 323]

IngredientFormSet = inlineformset_factory(
    parent_model=Food,
    model=Ingredient,
    form=IngredientForm,
    extra=1,  # Start with one empty form row
    can_delete=True,
    fk_name="complex_food"
)

MealConsumptionFormSet = inlineformset_factory(
    parent_model=Meal,
    model=MealConsumption,
    form=MealConsumptionForm,
    extra=1, 
    can_delete=True
)

# --- Listing foods ---
def list_meals(request, just_added=False):
    ''' Returns `meal_list.html` with the `selected_date` '''
    if just_added:
        datestr = request.POST.get('selected_date')
    else:
        datestr = request.GET.get('selected_date')
    day = get_or_create_day(request.user, datestr)
    meals = day.meals.all()
    print(f"{meals=}")
    for meal in meals:
        meal.nutrients = meal.get_nutrients_consumed()
    ctx = {
        "meals": meals,
        "date": datetime.strptime(datestr, '%Y-%m-%d').date(),
        "today": date.today(),
        "added": just_added
    }
    return render(request, "calcounter/meal_list.html", ctx)

def food_fingerprint(user, pantry_item):
    gender = user.profile.gender  # 'M' or 'F'
    age = user.profile.age  # integer
    if age < 19:
        goal_type = 'Young ' + 'Male' if gender == 'M' else 'Female'
    else:
        goal_type = 'Adult ' +  'Male' if gender == 'M' else 'Female'
    goals = {}
    for mineral, values in RDA_LOOKUP['Minerals'].items():
        goals[mineral] = values[goal_type]
    for vitamin, values in RDA_LOOKUP['Vitamins'].items():
        goals[vitamin] = values[goal_type]
 
    def get_ratio(value, goal):
        if not goal or goal == 0: return 0
        return min(float(value) / float(goal), 1.0) 

    if pantry_item.unit.name == "grams":
        serving = 100
    else:
        serving = float(pantry_item.unit.gram_weight)
    data = pantry_item.food.get_nutrition_consumed(serving)
    pantry_item.nutrients = data
    pantry_item.badges = pantry_item.food.get_badges()
    macros = [
        {"name": "Protein", "value": round(data['protein'])},
        {"name": "Fat",     "value": round(data['fat'])},
        {"name": "Carbs",   "value": round(data['carb']),
        "sugar": round(data['sugar']),
        "fiber": round(data['fiber'])},
    ]
    minerals = [
        {"name": "Na",     "ratio": get_ratio(data['sodium'],       goals['sodium']), "value": round(data['sodium'])},
        {"name": "K",  "ratio": get_ratio(data['potassium'],    goals['potassium']), "value": round(data['potassium'])},
        {"name": "Ca",    "ratio": get_ratio(data['calcium'],      goals['calcium']), "value": round(data['calcium'])},
        {"name": "Mg",  "ratio": get_ratio(data['magnesium'],    goals['magnesium']), "value": round(data['magnesium'])},
        {"name": "Zn",       "ratio": get_ratio(data['zinc'],         goals['zinc']), "value": round(data['zinc'])},
        {"name": "Fe",       "ratio": get_ratio(data['iron'],         goals['iron']), "value": round(data['iron'])},
    ]
    vitamins = [
        {"name": "A",   "ratio": get_ratio(data['vitamin_a'],   goals['A']), "value": round(data['vitamin_a'], 1)},
        {"name": "B6",  "ratio": get_ratio(data['vitamin_b6'],  goals['B6']), "value": round(data['vitamin_b6'], 1)},
        {"name": "B12", "ratio": get_ratio(data['vitamin_b12'], goals['B12']), "value": round(data['vitamin_b12'], 1)},
        {"name": "C",   "ratio": get_ratio(data['vitamin_c'],   goals['C']), "value": round(data['vitamin_c'], 1)},
        {"name": "D",   "ratio": get_ratio(data['vitamin_d'],   goals['D']), "value": round(data['vitamin_d'], 1)},
        {"name": "E",   "ratio": get_ratio(data['vitamin_e'],   goals['E']), "value": round(data['vitamin_e'], 1)},
    ]
    return macros, minerals, vitamins


def list_foods(request, action, just_added=False):
    ''' Returns `food_list.html` with the `selected_date` '''
    if action == 'all':
        foods = PantryItem.objects.prefetch_related(
            'food__ingredient_set__ingredient',
            'food__ingredient_set__unit'
        ).all()
    elif action == 'in_stock':
        foods = PantryItem.objects.select_related(
            'food', 'unit'
        ).exclude(status='o')
    elif action == 'complex':
        foods = PantryItem.objects.select_related(
            'food', 'unit'
        ).filter(
            food__ingredient__isnull=False
        ).distinct()
    elif action == 'simple':
        foods = PantryItem.objects.select_related('food', 'unit').filter(
        food__ingredient__isnull=True
        )
    print(f"{foods=}")

    for pantry_item in foods:
        macros, minerals, vitamins = food_fingerprint(request.user, pantry_item)
        pantry_item.macros = macros
        pantry_item.minerals = minerals
        pantry_item.vitamins = vitamins

    context = {
        "foods": foods,
        "added": just_added
    }
    return render(request, "calcounter/food_list.html", context)


def list_recipes(request):
    ''' return list of recipes '''
    recipes = Recipe.objects.filter(
        food__owner=request.user
    ).select_related('food')
    return render(request, 'calcounter/recipe_list.html', {'recipes': recipes})


# === CRUD : Adding Food/Meals ===

# --- Meals

def new_recipe(request):
    ''' return recipe entry form '''
    form = RecipeForm(request.POST or None, user=request.user)
    if request.POST and form.is_valid():
        form.save()
        return render(request, 'calcounter/recipe_area.html')
    return render(request, 'calcounter/recipe_entry.html', {'form': form, 'editing': False})

def add_meal(request):
    '''
        View for food form
        GET  : displays meal entry form
        POST : adds meal to given date, refresh meal list
    '''
    if request.POST:
        form = MealForm(request.POST)
        formset = MealConsumptionFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            # Save parent Meal
            meal = form.save(commit=False)
            meal.day = get_or_create_day(
                request.user, request.POST.get('selected_date'))
            meal.save()
            # Link children to parent and save
            instances = formset.save(commit=False)
            for instance in instances:
                instance.meal = meal
                instance.save()
            formset.save_m2m() # Required if there are ManyToMany relationships
            return list_meals(request, True)
        else:
            print("form invalid")
            print(form.errors)
            print(formset.errors)

    else:
        form = MealForm()
        formset = MealConsumptionFormSet()
    return render(request, 'calcounter/meal_entry.html', {'form': form, 'formset': formset})


def add_meal_row(request):
    ''' append a food to the current meal '''
    formset = MealConsumptionFormSet()
    # Return the 'empty_form' which uses __prefix__ as the ID placeholder
    return render(request, 'calcounter/meal_row.html', {'form': formset.empty_form})


def add_manual_meal_row(request):
    ''' append a food to the current meal '''
    formset = MealConsumptionFormSet()
    # Return the 'empty_form' which uses __prefix__ as the ID placeholder
    return render(request, 'calcounter/meal_manual_row.html', {'form': formset.empty_form})

# ----- Food

def new_search_food(request):
    ''' return `search_ingred` and oob swap `cancel` '''
    return render(request, 'calcounter/ingred_search_area.html')


def new_complex_food(request):
    if request.POST:
        form = FoodForm(request.POST)
        formset = IngredientFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            # Save parent Food
            complex_food = form.save(commit=False)
            complex_food.owner = request.user
            complex_food.save()
            # create gram unit for complex food
            gram, _ = FoodUnit.objects.get_or_create(
                food=complex_food,
                name="grams",
                defaults={'gram_weight': 1.0, 'is_standard': True}
            )
            PantryItem.objects.get_or_create(
                user=request.user,
                food=complex_food,
                unit=gram,
                amount=0
            )
            # Link children to parent and save
            total_grams = 0  # for 'As Prepared' foodunit
            nutrition = {}
            instances = formset.save(commit=False)
            for instance in instances:
                instance.complex_food = complex_food
                serving_size = instance.amount * float(instance.unit.gram_weight)
                total_grams += serving_size
                nutrition_instance = instance.ingredient.get_nutrition_consumed(serving_size)
                for key, value in nutrition_instance.items():
                    nutrition[key] = nutrition.get(key, 0) + value
                instance.save()
            if total_grams > 0:
                normalization_factor = 100 / total_grams
            else:
                normalization_factor = 0
            # 2. Update complex food nutrition normalized to 100g
            for key, value in nutrition.items():
                # Normalize the value to the 'per 100g' standard
                normalized_value = value * normalization_factor
                setattr(complex_food, key, normalized_value)
            complex_food.save()
            # create 'as prepared' unit
            FoodUnit.objects.get_or_create(
                food=complex_food,
                name="as prepared",
                defaults={'gram_weight': total_grams, 'is_standard': False}
            )
            formset.save_m2m() # Required if there are ManyToMany relationships
            return list_foods(request, 'complex', True)
        else:
            print("form invalid")
            print(form.errors)
            print(formset.errors)
    else:
        form = FoodForm()
        formset = IngredientFormSet()
    return render(request, 'calcounter/complex_food_entry.html', {'form': form, 'formset': formset})


def add_ingredient_row(request):
    formset = IngredientFormSet()
    # Return the 'empty_form' which uses __prefix__ as the ID placeholder
    return render(request, 'calcounter/ingredient_row.html', {'form': formset.empty_form})


def get_units_for_ingredient(request):
    food_id = request.GET.get('food_id')
    if not food_id:
        return HttpResponse('<option value="">Select food first</option>')
    units = FoodUnit.objects.filter(food_id=food_id)
    print(f"{units=}")
    return render(request, 'calcounter/unit_options.html', {'units': units})


def add_pantry_food(request, food_id):
    '''Add a new food to pantry (templates)'''
    food = get_object_or_404(Food, pk=food_id)
    # 1. Create the 'Grams' unit (every food should have this)
    FoodUnit.objects.get_or_create(
        food=food,
        name="grams",
        defaults={'gram_weight': 1.0, 'is_standard': True}
    )
    # if usda modifier info passed, save as food unit
    # otherwise, use default 100g
    modifier = request.POST.get('modifier')
    gram_weight = request.POST.get('gram_weight')
    print(f"{modifier=}, {gram_weight=}")
    if modifier and gram_weight:
        # 2. Create the custom unit 'cup', 'slice', etc
        usda_unit, _ = FoodUnit.objects.get_or_create(
            food=food,
            name=modifier,
            defaults={'gram_weight': float(gram_weight), 'is_standard': True}
        )
        print(f"{usda_unit=}")
        PantryItem.objects.create(
            user=request.user,
            food=food,
            unit=usda_unit,
            amount=1
        )
    else:
        PantryItem.objects.create(
            user=request.user,
            food=food,
            unit=FoodUnit.objects.get(food=food, name="grams"),
            amount=1
        )
    return list_foods(request, 'all')

def food_unit_modal(request, food_id):
    ''' return modal for editing food units '''
    food = get_object_or_404(Food, pk=food_id)
    pantry_item = PantryItem.objects.filter(food=food, user=request.user).first()
    if request.POST:
        new_name = request.POST.get('pantry_name')
        if pantry_item and new_name:
            pantry_item.name = new_name
            pantry_item.save()
        form = FoodUnitForm(request.POST)
        if form.is_valid():
            food_unit = form.save(commit=False)
            food_unit.food = food
            food_unit.save()
            print("saved food unit")
    foodunits = food.units.all()
    form = FoodUnitForm()
    context = {
        'food': food,
        'foodunits': foodunits,
        'form': form,
        'pantry_item': pantry_item
    }
    return render(request, 'calcounter/food_unit_modal.html', context)

def select_food_unit(request, food_id, unit_id):
    ''' set selected food unit for food '''
    food = get_object_or_404(Food, pk=food_id)
    unit = get_object_or_404(food.units, pk=unit_id)
    food.unit = unit
    food.save()
    return render(request, 'calcounter/checkmark.html')

def query_ingredient(request):
    query = request.GET.get('query')
    print(f"{query=}")
    if query == '':
        return HttpResponse('')
    include_branded = request.GET.get('branded') == 'on'
    include_foundational = request.GET.get('foundational') == 'on'
    # Map these to USDA data types
    data_types = []
    if include_branded:
        data_types.append("Branded&")
    if include_foundational:
        data_types.append("Foundation,SR%20Legacy&")
    if data_types == []:
        data_types = ["Foundation,SR%20Legacy"]
    url = (
        f"https://api.nal.usda.gov/fdc/v1/foods/search?"
        f"api_key={USDA_KEY}&"
        f"query='{query}'&"
        f"dataType={','.join(data_types)}"  # API filters for you
        f"pageSize=50" 
    )
    print(f"{url=}")
    r = requests.get(url)
    foods = r.json().get("foods", [])
    results = []
    for food in foods:
        print(f"{food["description"]=}")
        print(f"{food["fdcId"]=}\n")
        results.append({
            "name": food["description"],
            "fdcId": food["fdcId"]
        })
    return render(request, 'calcounter/ingred_search.html', {"foods": results})


def get_specific_usda_item(request, fdcId):
    single_url = f"https://api.nal.usda.gov/fdc/v1/food/{fdcId}?api_key={USDA_KEY}"
    foodItem = Food.objects.filter(fdc_id=fdcId).first()
    if not foodItem:
        item = requests.get(single_url).json()
        print("made request to USDA")
        # --- 1. Extract All Available Nutrients and Map by ID ---
        # - extract portion info
        portion = item.get("foodPortions", [])[0] if item.get("foodPortions", []) else {}
        portion_name = portion.get("modifier", "serving")
        portion_amt = portion.get("amount", 1)
        portion_gram = portion.get("gramWeight", 1)
        # 1 gram = no portion info
        print(f"{portion_gram} grams per {portion_amt} {portion_name}")
        # - extract nutrients
        all_nutrients = {}
        nutrients = item.get("foodNutrients", [])
        for n in nutrients:
            # n = {amounts, nutrient{number, name, unitName}}
            # n_info = nutrient{number, name, unitName}
            n_info = n.get("nutrient", n)
            nutrient_id = int(float(n_info.get("number", 0)))
            if nutrient_id in NUTRIENT_MAP.values():
                all_nutrients[nutrient_id] = {
                    "name":  n_info.get("name"),
                    "value": n.get("amount", 0.00),
                    "unit":  n_info.get("unitName", "N/A")
                }
                print(f"{all_nutrients[nutrient_id]=}")
        # --- Some foods don't have energy values, calculate instead ---
        cals = all_nutrients.get(208, {}).get("value", 0.0)
        if (cals == {} or cals == 0.0):
            # Atwater Factors calorie calculation 4-9-4
            protein = all_nutrients.get(203, {}).get('value', 0)
            fat = all_nutrients.get(204, {}).get('value', 0)
            carbs = all_nutrients.get(205, {}).get('value', 0)
            all_nutrients[208] = {
                "name": "Energy",
                "value": (protein * 4) + (fat * 9) + (carbs * 4),
                "unit": "kcal"
            }
        # --- Save the Food Item for future use
        foodItem = Food.objects.create(
            name=item.get("description"),
            fdc_id=fdcId,
            calories=int(all_nutrients.get(208, {}).get('value', 0)),
            protein=int(all_nutrients.get(203, {}).get('value', 0)),
            fat=int(all_nutrients.get(204, {}).get('value', 0)),
            carb=int(all_nutrients.get(205, {}).get('value', 0)),
            sugar=int(all_nutrients.get(269, {}).get('value', 0)),
            fiber=int(all_nutrients.get(291, {}).get('value', 0)),
            cholesterol=int(all_nutrients.get(601, {}).get('value', 0)),
            calcium=all_nutrients.get(301, {}).get('value', 0),
            iron=all_nutrients.get(303, {}).get('value', 0),
            magnesium=all_nutrients.get(304, {}).get('value', 0),
            potassium=all_nutrients.get(306, {}).get('value', 0),
            sodium=all_nutrients.get(307, {}).get('value', 0),
            zinc=all_nutrients.get(309, {}).get('value', 0),
            vitamin_a=all_nutrients.get(320, {}).get('value', 0),
            vitamin_b6=all_nutrients.get(415, {}).get('value', 0),
            vitamin_b12=all_nutrients.get(418, {}).get('value', 0),
            vitamin_c=all_nutrients.get(401, {}).get('value', 0),
            vitamin_d=all_nutrients.get(328, {}).get('value', 0),
            vitamin_e=all_nutrients.get(323, {}).get('value', 0),
        )
        FoodUnit.objects.get_or_create(
            food=foodItem,
            name=portion_name if portion_gram != 1 else "grams",
            defaults={'gram_weight': portion_gram, 'is_standard': True }
        )
    else:
        print("found existing food item in DB")
        unit = foodItem.units.first()
        portion_name = unit.name
        portion_gram = unit.gram_weight
        portion_amt = 1
    final_data = foodItem.to_formatted_dict()
    context = {
        'food': final_data,
        'food_id': foodItem.pk,
        'gram': portion_gram,
        'amount': portion_amt,
        'modifier': portion_name
    }
    return render(request, 'calcounter/ingred.html', context)


def meal_into_complexfood(request, meal_id):
    ''''''
    pass


# --- CRUD : Update a food ---

def update_pantry_item(request, item_id, action):
    pantry_item = get_object_or_404(PantryItem, id=item_id, user=request.user)
    
    # 1. Update Quantity or Unit
    if action == 'up':
        pantry_item.amount += 1
    elif action == 'down':
        pantry_item.amount = max(0, pantry_item.amount - 1)
    elif action == 'set':
        pantry_item.amount = float(request.POST.get('amount', 0))
    elif action == 'unit':
        unit_id = request.POST.get('unit_id')
        pantry_item.unit = get_object_or_404(FoodUnit, id=unit_id, food=pantry_item.food)

    # 2. Apply Status Logic
    if pantry_item.amount == 0:
        pantry_item.status = 'o' # OUT
    elif 0 < pantry_item.amount < 4:
        pantry_item.status = 'l' # LOW
    else:
        pantry_item.status = 's' # IN STOCK
        
    pantry_item.save()

    macros, minerals, vitamins = food_fingerprint(request.user, pantry_item)
    pantry_item.macros = macros
    pantry_item.minerals = minerals
    pantry_item.vitamins = vitamins

    # need to recalculate bades, nutrients
    # 3. Return the updated snippet
    # We re-render the individual LI so the detail state and status update correctly
    return render(request, 'calcounter/food.html', {'pantry': pantry_item, 'open': True})


def edit_unit(request, unit_id):
    unit = get_object_or_404(FoodUnit, id=unit_id)
    
    if request.method == 'POST':
        unit.name = request.POST.get('name')
        unit.gram_weight = request.POST.get('gram_weight')
        unit.save()
        # Return the READ-ONLY snippet (the code from Step 1)
        return render(request, 'calcounter/unit_display_row.html', {'unit': unit})
    
    # Return the EDIT FORM snippet (Step 2)
    return render(request, 'calcounter/unit_edit_form.html', {'unit': unit})

def get_unit(request, unit_id):
    # This handles the "Cancel" button
    unit = get_object_or_404(FoodUnit, id=unit_id)
    return render(request, 'calcounter/unit_display_row.html', {'unit': unit})


def update_recipe(request, recipe_id):
    if request.POST:
        recipe = get_object_or_404(Recipe, id=recipe_id)
        form = RecipeForm(request.POST, instance=recipe, user=request.user)
        if form.is_valid():
            form.save()
            return render(request, 'calcounter/recipe_area.html')
    recipe = get_object_or_404(Recipe, id=recipe_id)
    form = RecipeForm(instance=recipe, user=request.user)
    return render(request, 'calcounter/recipe_entry.html', {'form': form, 'recipe': recipe, 'editing': True })


# --- Display ---

def get_type_of_input(request):
    return render(request, 'calcounter/food_type_input.html')

def get_meal_type_of_input(request):
    return render(request, 'calcounter/meal_type_input.html')

def get_food_input(request):
    return render(request, 'calcounter/food_entry_button.html')

def get_search_area(request):
    return render(request, 'calcounter/ingred_search_area.html')


def cancel_form_m(request):
    ''' Returns `entry_buttons` template '''
    return render(request, "calcounter/meal_entry_button.html")


def cancel_form_f(request):
    ''' Returns `entry_buttons` template '''
    return render(request, "calcounter/food_type_input.html")

def clear(request):
    ''' returns empty response to clear target '''
    return HttpResponse("")


# CRUD : Deleteing food

def delete_meal(request, meal_id):
    ''' delete meal '''
    meal = get_object_or_404(Meal, id=meal_id)
    meal.delete()
    return clear(request)

def delete_food(request, pantry_id):
    ''' delete pantry food entry
    1. if pantryitem is complex food:
      - if food is used in meals or recipes, just remove pantryitem, set is_active=false
      - else, delete pantryitem and food
    2. if pantryitem is simple food: just delete pantryitem
    ''' 
    pantry_item = get_object_or_404(PantryItem, id=pantry_id)
    underlying_food = pantry_item.food
    # check if food is used in meals or recipes
    delete, mark = False, False
    used_in_meals = MealConsumption.objects.filter(food=underlying_food).exists()
    used_in_recipes = Recipe.objects.filter(food=underlying_food).exists()
    if not used_in_meals and not used_in_recipes:
        if underlying_food.owner == request.user:
            delete = True
    # food is used elsewhere, just mark inactive
    if underlying_food.owner == request.user:
        mark = True
    # food is a simple food, just delete pantry item
    pantry_item.delete()
    if delete:
        underlying_food.delete()
    elif mark:
        underlying_food.is_active = False
        underlying_food.save()
    return clear(request)
    

def delete_unit(request, unit_id):
    unit = get_object_or_404(FoodUnit, id=unit_id)
    unit.delete()
    return clear(request)


def delete_recipe(request, recipe_id):
    ''' Delete a saved recipe '''
    recipe = get_object_or_404(Recipe, id=recipe_id)
    recipe.delete()
    return clear(request)
