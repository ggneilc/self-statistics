"""
    Calcounter manages Food
"""
from django.shortcuts import get_object_or_404, render, HttpResponse
from django.db.models import Sum
from .models import Food, Meal, Ingredient, MealConsumption, PantryItem
from .forms import FoodForm, MealForm, MealConsumptionFormSet
from core.utils import get_or_create_day

from copy import copy
from datetime import datetime
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


# --- Listing foods ---
def meal_area(request):
    ''' meal log fills #change with container & entry '''
    return render(request, 'calcounter/meal_area.html')


def food_area(request):
    ''' pantry fills #change with container & entry '''
    return render(request, 'calcounter/food_area.html')


def list_meals(request):
    ''' Returns `meal_list.html` with the `selected_date` '''
    day = get_or_create_day(request.user, request.GET['selected_date'])
    meals = day.meals.all()
    print(f"{meals=}")
    # Mark meals made from templates as saved
    for food in meals:
        food.is_template = Food.objects.filter(
            name=food.name, is_template=True).exists()
    context = {"foods": meals}
    return render(request, "calcounter/meal_list.html", context)


def list_foods(request):
    ''' Returns `food_list.html` with the `selected_date` '''
#    foods = Food.objects.available_to_user(request.user)
    # Mark meals made from templates as saved
    foods = PantryItem.objects.filter(user=request.user)
    print(f"{foods=}")               # PantryItem objects
    context = {"foods": foods}
    return render(request, "calcounter/food_list.html", context)


def list_meal_templates(request):
    ''' returns `template_list.html` with meal templates '''
    meals = Meal.objects.filter(day__user=request.user)
    template_meals = [f for f in meals if f.is_template]
    if len(template_meals) == 0:      # if no templates, return entry form
        return add_meal(request)
    context = {'foods': template_meals}
    return render(request, "calcounter/template_list.html", context)


def list_food_templates(request):
    ''' Returns `template_list.html` with pantry foods '''
    foods = Food.objects.filter(day__user=request.user)
    template_meals = [f for f in foods if f.is_template]
    if len(template_meals) == 0:      # if no templates, return entry form
        return add_meal(request)
    context = {'foods': template_meals}
    return render(request, "calcounter/template_list.html", context)

# === CRUD : Adding Food/Meals ===

# --- Meals


def add_meal(request):
    '''
        View for food form
        GET  : displays meal entry form
        POST : adds meal to given date, refresh meal list
    '''
    if request.POST:
        pass
    else:
        form = MealForm()
        context = {
            "form": form,
            "date": request.GET.get('selected_date')
        }
    return render(request, "calcounter/meal_entry.html", context)


def add_food_to_meal(request, fdc_id):
    ''' append a food to the current meal '''
    if request.POST:
        fdc_id = request.POST.get('fdc_id')
        food_item = Food.objects.get(fdc_id=fdc_id)
        formset = MealConsumptionFormSet(
            request.POST, prefix='mealconsumption_set')
        new_form = formset.empty_form
        new_form.initial['food'] = food_item.pk
        new_form.initial['food_name'] = food_item.name
        context = {
            "form": new_form,
            "food_name": food_item.name,
            "prefix": formset.prefix,
            "empty_form_index": formset.total_form_count()
        }
        return render(request, 'calcounter/meal_row.html', context)
    return HttpResponse(status=400)

# --- Food


def add_food(request):
    '''simple or complex selection'''
    pass


def register_food(request):
    '''save info for a Food / 100g'''
    pass


def new_search_food(request):
    ''' return `search_ingred` and oob swap `cancel` '''
    return render(request, 'calcounter/ingred_search_area.html')


def new_complex_food():
    pass


def add_pantry_food(request, food_id):
    '''Add a new food to pantry (templates)'''
    food = get_object_or_404(Food, pk=food_id)
    item = PantryItem.objects.create(
        user=request.user,
        food=food,
    )
    return list_foods(request)


def query_ingredient(request):
    query = request.POST.get('query')
    print(f"{query=}")
    if query == '':
        return HttpResponse('')
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={
        USDA_KEY}&query={query}"
    r = requests.get(url)
    foods = r.json().get("foods", [])
    results = []
    for food in foods:
        # Only foundational foods
        if food.get("dataType") not in ("Foundation", "SR Legacy"):
            continue
        print(f"{food["description"]=}")
        print(f"{food["fdcId"]=}\n")
        results.append({
            "name": food["description"],
            "fdcId": food["fdcId"]
        })
    return render(request, 'calcounter/ingred_search.html', {"foods": results})


def get_specific_usda_item(request, fdcId):
    single_url = f"https://api.nal.usda.gov/fdc/v1/food/{
        fdcId}?format=abridged&api_key={USDA_KEY}"
    foodItem = Food.objects.filter(fdc_id=fdcId).first()
    if not foodItem:
        item = requests.get(single_url).json()
        print("made request to USDA")
        # --- 1. Extract All Available Nutrients and Map by ID ---
        all_nutrients = {}
        nutrients = item.get("foodNutrients", [])
        for n in nutrients:
            nutrient_id = int(float(n.get("number", 0)))
            if nutrient_id in NUTRIENT_MAP.values():
                all_nutrients[nutrient_id] = {
                    "name":  n.get("name"),
                    "value": n.get("amount", 0.00),
                    "unit":  n.get("unitName", "N/A")
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
#   final_data = {
#        "fdc_id": self.fdc_id,
#        "name": self.name,
#        "macros": {},
#        "minerals": {},
#        "vitamins": {}
#   }
    final_data = foodItem.to_formatted_dict()
    context = {
        'food': final_data,
        'food_id': foodItem.pk
    }
    return render(request, 'calcounter/ingred.html', context)


# --- CRUD : Update a food ---


def edit_food(request, food_id):
    food = get_object_or_404(Food, id=food_id)
    return render(request, 'calcounter/meal_edit.html', {"food": food})


def update_food(request, food_id):
    food = get_object_or_404(Food, id=food_id)
    food.calories = request.POST['calories']
    food.protein = request.POST['protein']
    food.fat = request.POST['fat'] or None
    food.carb = request.POST['carb'] or None
    food.save()
    food.is_template = Food.objects.filter(
        name=food.name, is_template=True).exists()
    return render(request, 'calcounter/meal.html', {"food": food})


def save_template(request, food_id):
    food = get_object_or_404(Food, id=food_id)
    food.is_template = True
    food.save()
    return render(request, 'calcounter/checkmark.html')


# --- Display ---

def get_type_of_input(request):
    return render(request, 'calcounter/meal_type_input.html')


def get_food_input(request):
    return render(request, 'calcounter/food_entry_button.html')


def get_auto_buttons(request):
    return render(request, 'calcounter/meal_auto_buttons.html')


def get_search_area(request):
    return render(request, 'calcounter/ingred_search_area.html')


def cancel_form_m(request):
    ''' Returns `entry_buttons` template '''
    return render(request, "calcounter/meal_entry_button.html")


def cancel_form_f(request):
    ''' Returns `entry_buttons` template '''
    return render(request, "calcounter/food_entry_button.html")


# render food in open state
def render_food(request, food_id):
    food = get_object_or_404(Food, id=food_id)
    food.is_template = Food.objects.filter(
        name=food.name, is_template=True).exists()
    return render(request, 'calcounter/meal.html', {
        "food": food,
        "just_updated": True})


def meal_update(request, day, rm=False):
    '''
        returns `meal_update.html` to oob-swap `totals` and `meal_list`.
        Called after add/delete of food.
        add : returns entry buttons to caller
        rm  : returns "" to caller
    '''
    foods = Food.objects.filter(day=day)
    totals = foods.aggregate(
        calories=Sum('calories'),
        protein=Sum('protein')
    )
    for food in foods:
        food.is_template = Food.objects.filter(
            name=food.name, is_template=True).exists()
    print("returning meal and totals")
    context = {
        "foods": foods,
        "calories": totals['calories'] or 0,
        "protein": totals['protein'] or 0,
    }
    if rm:  # content inserted into meal
        return render(request, 'calcounter/meal_update_rm.html', context)
    else:
        return render(request, 'calcounter/meal_list.html', context)


# CRUD : Deleteing food


def delete_food(request, food_id):
    '''
        Delete food entry:
        - todo: find way to keep date selected
    '''
    food = get_object_or_404(Food, id=food_id)
    day = food.day
    # Don't delete food entry that is the template
    if food.is_template:
        food.day = get_or_create_day(request.user, datetime(1, 1, 1))
        food.save()
        return meal_update(request, day, rm=True)
    food.delete()
    return meal_update(request, day, rm=True)


def delete_food_template(request, food_id):
    '''
        Delete a saved food template
    '''
    food = get_object_or_404(Food, id=food_id)
    food.is_template = False
    food.save()
    return HttpResponse("")
