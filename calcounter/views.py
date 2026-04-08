"""
    Calcounter manages Food
"""
from django.shortcuts import get_object_or_404, render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Prefetch
from django.forms.models import inlineformset_factory
from .models import Food, Meal, Ingredient, MealConsumption, PantryItem, FoodUnit, Recipe
from .forms import FoodForm, FoodUnitForm, MealForm, IngredientForm, MealConsumptionForm, RecipeForm
from .utils import (
    NUTRIENT_MAP,
    MACRO,
    MINERAL,
    VITAMIN,
    BRANDED_VITAMIN_FALLBACKS,
    food_fingerprint,
    meal_fingerprint
)
from core.utils import get_or_create_day
from copy import copy
from datetime import datetime, date
import requests
import os

USDA_KEY = os.getenv('USDA_API_KEY')

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
@login_required
def list_meals(request, just_added=False):
    ''' Returns `meal_list.html` with the `selected_date` '''
    datestr = request.GET.get('selected_date') if not just_added else request.POST.get('selected_date')
    day = request.user.days.get(date=datestr)
    meals = day.meals.prefetch_related('items__food', 'items__unit').all()
    print(f"{meals=}")
    for meal in meals:
        meal.nutrients = meal.get_nutrients_consumed()
        macros, minerals, vitamins = meal_fingerprint(request.user, meal.nutrients)
        meal.macros = macros
        meal.minerals = minerals
        meal.vitamins = vitamins
        meal.macro_script_id = f"macros-{meal.id}"
        meal.mineral_script_id = f"minerals-{meal.id}"
        meal.vitamin_script_id = f"vitamins-{meal.id}"
    ctx = {
        "meals": meals,
        "date": datetime.strptime(datestr, '%Y-%m-%d').date(),
        "today": date.today(),
    }
    return render(request, "calcounter/meal_list.html", ctx)

@login_required
def list_foods(request, action, just_added=False):
    accessible_units = FoodUnit.objects.accessible_to(request.user)
    queryset = PantryItem.objects.filter(user=request.user).select_related('food', 'unit')

    if action == 'all':
        foods = queryset.prefetch_related(
            Prefetch('food__units', queryset=accessible_units),
            Prefetch('food__ingredient_set__unit', queryset=accessible_units),
            'food__ingredient_set__ingredient',
        )
    elif action == 'in_stock':
        foods = queryset.exclude(status='o').prefetch_related(
            Prefetch('food__units', queryset=accessible_units)
        )
    elif action == 'complex':
        foods = queryset.filter(food__ingredient__isnull=False).distinct().prefetch_related(
            Prefetch('food__units', queryset=accessible_units)
        )
    elif action == 'simple':
        foods = queryset.filter(food__ingredient__isnull=True).prefetch_related(
            Prefetch('food__units', queryset=accessible_units)
        )
    else:
        foods = queryset.none()
    print(f"Fetched {foods.count()} items for action: {action}")

    for pantry_item in foods:
        macros, minerals, vitamins = food_fingerprint(request.user, pantry_item)
        pantry_item.macros = macros
        pantry_item.minerals = minerals
        pantry_item.vitamins = vitamins
        pantry_item.macro_script_id = f"macros-{pantry_item.id}"
        pantry_item.mineral_script_id = f"minerals-{pantry_item.id}"
        pantry_item.vitamin_script_id = f"vitamins-{pantry_item.id}"

    context = {
        "foods": foods,
        "added": just_added
    }
    return render(request, "calcounter/food_list.html", context)


#TODO : add a view list single food for modal updates
#TODO : add a view to list foods by class

@login_required
def list_recipes(request):
    ''' return list of recipes '''
    recipes = Recipe.objects.filter(
        food__owner=request.user
    ).select_related('food')
    return render(request, 'calcounter/recipe_list.html', {'recipes': recipes})


# === CRUD : Adding Food/Meals ===

# --- Meals

@login_required
def new_recipe(request):
    ''' return recipe entry form '''
    form = RecipeForm(request.POST or None, user=request.user)
    if request.POST and form.is_valid():
        form.save()
        response = render(request, 'calcounter/recipe_area.html')
        response['HX-Trigger'] = 'recipeCreated'
        return response
    return render(request, 'calcounter/recipe_entry.html', {'form': form, 'editing': False})

@login_required
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
            response = list_meals(request, True)
            response['HX-Trigger'] = 'mealCreated'
            return response
        else:
            return render(request, 'calcounter/meal_entry.html', {'form': form, 'formset': formset})
    form = MealForm()
    formset = MealConsumptionFormSet()
    return render(request, 'calcounter/meal_entry.html', {'form': form, 'formset': formset})

@login_required
def add_meal_row(request):
    ''' append a food to the current meal '''
    formset = MealConsumptionFormSet()
    # Return the 'empty_form' which uses __prefix__ as the ID placeholder
    return render(request, 'calcounter/meal_row.html', {'form': formset.empty_form})

@login_required
def add_manual_meal_row(request):
    ''' append a food to the current meal '''
    formset = MealConsumptionFormSet()
    # Return the 'empty_form' which uses __prefix__ as the ID placeholder
    return render(request, 'calcounter/meal_manual_row.html', {'form': formset.empty_form})

# ----- Food

@login_required
def new_search_food(request):
    ''' return `search_ingred` and oob swap `cancel` '''
    return render(request, 'calcounter/ingred_search_area.html')

@login_required
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
            response = list_foods(request, 'complex', True)
            response['HX-Trigger'] = 'pantryItemAdded'
            return response
        else:
            print("form invalid")
            print(form.errors)
            print(formset.errors)
    else:
        form = FoodForm()
        formset = IngredientFormSet()
    return render(request, 'calcounter/complex_food_entry.html', {'form': form, 'formset': formset})

@login_required
def add_ingredient_row(request):
    formset = IngredientFormSet()
    # Return the 'empty_form' which uses __prefix__ as the ID placeholder
    return render(request, 'calcounter/ingredient_row.html', {'form': formset.empty_form})

@login_required
def get_units_for_ingredient(request):
    food_id = request.GET.get('food_id')
    if not food_id:
        return HttpResponse('<option value="">Select food first</option>')
    units = FoodUnit.objects.accessible_to(request.user).filter(food_id=food_id)
    print(f"{units=}")
    return render(request, 'calcounter/unit_options.html', {'units': units})

@login_required
def typeahead_foods(request):
    q = (request.GET.get('q') or '').strip()
    target_hidden_id = request.GET.get('target_hidden_id') or ''
    target_input_id = request.GET.get('target_input_id') or ''
    target_unit_id = request.GET.get('target_unit_id') or ''

    foods = []
    if q:
        foods = (
            Food.objects.available_to_user(request.user)
            .filter(is_active=True, name__icontains=q)
            .order_by('name')[:20]
        )

    ctx = {
        "foods": foods,
        "target_hidden_id": target_hidden_id,
        "target_input_id": target_input_id,
        "target_unit_id": target_unit_id,
    }
    return render(request, "calcounter/typeahead_food_results.html", ctx)

@login_required
def add_pantry_food(request, food_id):
    '''Add a new food to pantry (templates)'''
    food = get_object_or_404(Food.objects.available_to_user(request.user), pk=food_id)
    food_name = food.name.split(', ')
    if len(food_name) > 1:
        food_name = food_name[1] + ' ' + food_name[0]
    else:
        food_name = food.name
    PantryItem.objects.get_or_create(
        user=request.user,
        food=food,
        name=food_name,
        unit=FoodUnit.objects.get(food=food, name="grams"),
        amount=1
    )
    response = list_foods(request, 'all')
    response['HX-Trigger'] = 'pantryItemAdded'
    return response

@login_required
def food_unit_modal(request, food_id):
    ''' return modal for editing food units '''
    pantry_item = get_object_or_404(PantryItem, pk=food_id, user=request.user)
    if request.POST:
        form = FoodUnitForm(request.POST)
        if form.is_valid():
            food_unit = form.save(commit=False)
            food_unit.creator = request.user
            food_unit.food = pantry_item.food
            food_unit.save()
            return render(request, 'calcounter/unit_display_row.html', {'unit': food_unit, 'pantry_id': pantry_item.id})

    food = pantry_item.food.to_formatted_dict()
    foodunits = pantry_item.food.units.accessible_to(request.user)
    form = FoodUnitForm()
    context = {
        'food': food,
        'foodunits': foodunits,
        'form': form,
        'pantry_item': pantry_item
    }
    return render(request, 'calcounter/food_unit_modal.html', context)

@login_required
def select_food_unit(request, food_id, unit_id):
    ''' set selected food unit for food '''
    food = get_object_or_404(Food, pk=food_id, owner=request.user)
    unit = get_object_or_404(food.units, pk=unit_id)
    food.unit = unit
    food.save()
    return render(request, 'calcounter/checkmark.html')

@login_required
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
        data_types.append("Branded")
    if include_foundational:
        data_types.append("Foundation,SR%20Legacy")
    if data_types == []:
        data_types = ["Foundation,SR%20Legacy"]
    url = (
        f"https://api.nal.usda.gov/fdc/v1/foods/search?"
        f"api_key={USDA_KEY}&"
        f"query='{query}'&"
        f"dataType={','.join(data_types)}&"
        f"pageSize=50&"
        f"format=abridged"
    )
    print(f"{url=}")
    r = requests.get(url)
    foods = r.json().get("foods", [])
    results = []
    nutrient_keys = {"208": "calories", "203": "protein", "204": "fat", "205": "carbs"}
    for food in foods:
        brand = food.get("brandName") or food.get("brandOwner") or ""
        entry = {
            "name": food["description"],
            "brand": brand,
            "fdcId": food["fdcId"],
            "calories": 0, "protein": 0, "fat": 0, "carbs": 0,
        }
        for n in food.get("foodNutrients", []):
            key = nutrient_keys.get(str(n.get("nutrientNumber", "")))
            if key:
                entry[key] = int(n.get("value", 0))
        if entry["calories"] == 0:
            entry["calories"] = entry["protein"] * 4 + entry["fat"] * 9 + entry["carbs"] * 4
        results.append(entry)
    return render(request, 'calcounter/ingred_search.html', {"foods": results})


def parse_usda_nutrients(item):
    all_nutrients = {}
    nutrients = item.get("foodNutrients", [])
    for n in nutrients:
        # n = {amounts, nutrient{number, name, unitName}}
        # n_info = nutrient{number, name, unitName}
        n_info = n.get("nutrient", n)
        nutrient_id = n_info.get("number", "")
        if nutrient_id in NUTRIENT_MAP.values():
            # Branded vitamin fallback: convert IU -> µg and store under standard ID
            if nutrient_id in BRANDED_VITAMIN_FALLBACKS:
                fallback = BRANDED_VITAMIN_FALLBACKS[nutrient_id]
                std_id = fallback["standard_id"]
                # Only use fallback if we don't already have the standard value
                if std_id not in all_nutrients:
                    converted = fallback["convert"](n.get("amount", 0.0))
                    all_nutrients[std_id] = {
                        "name":  n_info.get("name"),
                        "value": round(converted, 2),
                        "unit":  "µg"
                    }
                    print(f"Branded fallback: {nutrient_id} -> {std_id}, {all_nutrients[std_id]=}")
            else:
                all_nutrients[nutrient_id] = {
                    "name":  n_info.get("name"),
                    "value": n.get("amount", 0.00),
                    "unit":  n_info.get("unitName", "N/A")
                }
                print(f"{all_nutrients[nutrient_id]=}")
    # --- Some foods don't have energy values, calculate instead ---
    cals = all_nutrients.get("208", {}).get("value", 0.0)
    if (cals == {} or cals == 0.0):
        # Atwater Factors calorie calculation 4-9-4
        protein = all_nutrients.get("203", {}).get('value', 0)
        fat = all_nutrients.get("204", {}).get('value', 0)
        carbs = all_nutrients.get("205", {}).get('value', 0)
        all_nutrients["208"] = {
            "name": "Energy",
            "value": (protein * 4) + (fat * 9) + (carbs * 4),
            "unit": "kcal"
        }

    servings = []
    # attempt to retrieve serving size
    serving_sizes = item.get("foodPortions", [])
    if serving_sizes:
        for serving_size in serving_sizes:
            gram_weight = serving_size.get("gramWeight", 0)
            amount = serving_size.get("amount", 1)
            modifier = serving_size.get("modifier", "")
            if gram_weight > 0 and amount > 0 and modifier:
                servings.append({
                    "gram_weight": gram_weight,
                    "modifier": str(amount) + " " + modifier
                })
    else:
        # branded food
        servingSize = item.get("servingSize", 0)
        if servingSize > 0:
            servings.append({
                "gram_weight": servingSize,
                "modifier": "serving"
            })

    return all_nutrients, servings

def query_usda_food(fdcId: str, abridged: bool = False) -> requests.Response:
    nutrient_ids = list(NUTRIENT_MAP.values())
    params = {
        'fdcIds': [fdcId],
        'api_key': USDA_KEY,
        'nutrients': nutrient_ids  
    }
    if abridged:
        params['format'] = 'abridged'
    response = requests.get("https://api.nal.usda.gov/fdc/v1/foods", params=params)
    return response

@login_required
def get_specific_usda_item(request, fdcId):
    foodItem = Food.objects.filter(fdc_id=fdcId).first()
    if not foodItem:
        # Attempt to query full API first, then fallback to abridged

        response = query_usda_food(fdcId)
        if response.status_code != 200:
            print(f"Error fetching USDA data: {response.status_code}")
            return HttpResponse("Error fetching USDA data")
        # returns in format : [ {food} ] : need error handling for empty list
        foods = response.json()
        if len(foods) == 0:
            response = query_usda_food(fdcId, abridged=True)
            if response.status_code != 200:
                print(f"Error fetching USDA data: {response.status_code}")
                return HttpResponse("Error fetching USDA data")
            foods = response.json()
            if len(foods) == 0:
                print(f"No food found for fdcId: {fdcId}")
                return HttpResponse("No food found for fdcId")
        food = foods[0]
        all_nutrients, servings = parse_usda_nutrients(food)
        # --- Save the Food Item for future use
        foodItem = Food.objects.create(
            name=food.get("description"),
            fdc_id=fdcId,
            calories=int(all_nutrients.get("208", {}).get('value', 0)),
            protein=int(all_nutrients.get("203", {}).get('value', 0)),
            fat=int(all_nutrients.get("204", {}).get('value', 0)),
            carb=int(all_nutrients.get("205", {}).get('value', 0)),
            sugar=int(all_nutrients.get("269", {}).get('value', 0)),
            fiber=int(all_nutrients.get("291", {}).get('value', 0)),
            cholesterol=int(all_nutrients.get("601", {}).get('value', 0)),
            calcium=all_nutrients.get("301", {}).get('value', 0),
            iron=all_nutrients.get("303", {}).get('value', 0),
            magnesium=all_nutrients.get("304", {}).get('value', 0),
            potassium=all_nutrients.get("306", {}).get('value', 0),
            sodium=all_nutrients.get("307", {}).get('value', 0),
            zinc=all_nutrients.get("309", {}).get('value', 0),
            vitamin_a=all_nutrients.get("320", {}).get('value', 0),
            vitamin_b6=all_nutrients.get("415", {}).get('value', 0),
            vitamin_b12=all_nutrients.get("418", {}).get('value', 0),
            vitamin_c=all_nutrients.get("401", {}).get('value', 0),
            vitamin_d=all_nutrients.get("328", {}).get('value', 0),
            vitamin_e=all_nutrients.get("323", {}).get('value', 0),
        )
        # create standard grams unit for food
        FoodUnit.objects.get_or_create(
            food=foodItem,
            name="grams",
            defaults={'gram_weight': 1, 'is_standard': True }
        )
        if servings:
            for serving in servings:
                FoodUnit.objects.get_or_create(
                    food=foodItem,
                    name=serving["modifier"],
                    defaults={'gram_weight': serving["gram_weight"], 'is_standard': True }
                )
    final_data = foodItem.to_formatted_dict()
    context = {
        'food': final_data,
        'food_id': foodItem.pk,
        'gram': 100,
        'amount': 1,
        'modifier': "serving"
    }
    return render(request, 'calcounter/ingred.html', context)


@login_required
def meal_into_complexfood(request, meal_id):
    ''''''
    pass


# --- CRUD : Update a food ---

def update_pantry_name(request, pantry_id):
    pantry_item = get_object_or_404(PantryItem, id=pantry_id, user=request.user)
    new_name = request.POST.get('pantry_name')
    if pantry_item and new_name:
        pantry_item.name = new_name
        pantry_item.save()
    resp = HttpResponse(200)
    resp['HX-Trigger'] = 'pantryItemUpdated'
    return resp

@login_required
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
    pantry_item.macro_script_id = f"macros-{pantry_item.id}"
    pantry_item.mineral_script_id = f"minerals-{pantry_item.id}"
    pantry_item.vitamin_script_id = f"vitamins-{pantry_item.id}"

    return render(request, 'calcounter/food.html', {'pantry': pantry_item, 'open': True})

@login_required
def edit_unit(request, pantry_id, unit_id):
    pantry_item = get_object_or_404(PantryItem, id=pantry_id, user=request.user)
    unit = get_object_or_404(FoodUnit, id=unit_id, food=pantry_item.food)
    
    if request.method == 'POST':
        unit.name = request.POST.get('name')
        unit.gram_weight = request.POST.get('gram_weight')
        unit.save()
        # Return the READ-ONLY snippet (the code from Step 1)
        response = render(request, 'calcounter/unit_display_row.html', {'unit': unit, 'pantry_id': pantry_id})
        response['HX-Trigger'] = 'pantryItemUpdated'
        return response
    
    # Return the EDIT FORM snippet (Step 2)
    return render(request, 'calcounter/unit_edit_form.html', {'unit': unit, 'pantry_id': pantry_id})

@login_required
def get_unit(request, pantry_id, unit_id):
    # This handles the "Cancel" button
    pantry_item = get_object_or_404(PantryItem, id=pantry_id, user=request.user)
    unit = get_object_or_404(FoodUnit, id=unit_id, food=pantry_item.food)
    return render(request, 'calcounter/unit_display_row.html', {'unit': unit, 'pantry_id': pantry_id})

@login_required
def update_recipe(request, recipe_id):
    if request.POST:
        recipe = get_object_or_404(Recipe, id=recipe_id, food__owner=request.user)
        form = RecipeForm(request.POST, instance=recipe, user=request.user)
        if form.is_valid():
            form.save()
            return render(request, 'calcounter/recipe_area.html')
    recipe = get_object_or_404(Recipe, id=recipe_id, food__owner=request.user)
    form = RecipeForm(instance=recipe, user=request.user)
    return render(request, 'calcounter/recipe_entry.html', {'form': form, 'recipe': recipe, 'editing': True })


# --- Display ---

@login_required
def get_type_of_input(request):
    return render(request, 'calcounter/food_type_input.html')

@login_required
def get_meal_type_of_input(request):
    return render(request, 'calcounter/meal_type_input.html')

@login_required
def get_food_input(request):
    return get_type_of_input(request)

@login_required
def get_search_area(request):
    return render(request, 'calcounter/ingred_search_area.html')

def get_recipe_area(request):
    return render(request, 'calcounter/recipe_area.html')

@login_required
def cancel_form_m(request):
    ''' Returns `entry_buttons` template '''
    return clear(request)

@login_required
def cancel_form_f(request):
    ''' Returns `entry_buttons` template '''
    return render(request, "calcounter/food_type_input.html")

@login_required
def clear(request):
    ''' returns empty response to clear target '''
    return HttpResponse("")


# CRUD : Deleteing food

@login_required
def delete_meal(request, meal_id):
    ''' delete meal '''
    meal = get_object_or_404(Meal, id=meal_id, day__user=request.user)
    meal.delete()
    return clear(request)

@login_required
def delete_food(request, pantry_id):
    ''' delete pantry food entry
    1. if pantryitem is complex food:
      - if food is used in meals or recipes, just remove pantryitem, set is_active=false
      - else, delete pantryitem and food
    2. if pantryitem is simple food: just delete pantryitem
    ''' 
    print(f"deleting {pantry_id=}")
    pantry_item = get_object_or_404(PantryItem, id=pantry_id)
    print(f"pantry_item={pantry_item}")
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
    print(f"deleted {pantry_id=}")
    return clear(request)
    
@login_required
def delete_unit(request, pantry_id, unit_id):
    pantry_item = get_object_or_404(PantryItem, id=pantry_id, user=request.user)
    unit = get_object_or_404(FoodUnit, id=unit_id, food=pantry_item.food)
    unit.delete()
    return clear(request)

@login_required
def delete_recipe(request, recipe_id):
    ''' Delete a saved recipe '''
    recipe = get_object_or_404(Recipe, id=recipe_id, food__owner=request.user)
    recipe.delete()
    return clear(request)
