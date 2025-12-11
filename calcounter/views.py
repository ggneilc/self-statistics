"""
    Calcounter manages Food
"""
from django.shortcuts import get_object_or_404, render, HttpResponse
from django.db.models import Sum
from .models import Food
from .forms import FoodForm
from core.utils import get_or_create_day

from copy import copy
from datetime import datetime
import requests
import os

USDA_KEY = os.getenv('USDA_API_KEY')

# Listing foods


def get_food(request):
    ''' Returns `meal_list.html` with the `selected_date` '''
    day = get_or_create_day(request.user, request.GET['selected_date'])
    foods = day.meals.all()
    print(f"{foods=}")
    # dont allow saving foods that are already templates
    for food in foods:
        food.is_template = Food.objects.filter(
            name=food.name, is_template=True).exists()
    context = {"foods": foods}
    return render(request, "calcounter/meal_list.html", context)


def get_food_templates(request):
    ''' Returns `template_list.html` with `request.user` templates '''
    meals = Food.objects.filter(day__user=request.user)
    template_meals = [f for f in meals if f.is_template]
    if len(template_meals) == 0:      # if no templates, return entry form
        return add_food(request)
    context = {'foods': template_meals}
    return render(request, "calcounter/template_list.html", context)


# CRUD : Adding Food

def add_food(request):
    '''
        View for food form
        GET  : displays meal entry form
        POST : adds meal to given date, refresh meal list
    '''
    if request.POST:
        f = FoodForm(request.POST)
        if f.is_valid():
            new_food = f.save(commit=False)
            new_food.user = request.user
            new_food.day = get_or_create_day(
                request.user, request.POST['selected_date'])
            if request.POST['action'] == 'save_template':
                new_food.is_template = True
            new_food.save()
            print("Saved new food")
            return meal_update(request, new_food.day)
    else:
        form = FoodForm()
        context = {
            "form": form,
            "date": request.GET.get('selected_date')
        }
    return render(request, "calcounter/meal_entry.html", context)


def add_food_template(request, food_id):
    '''
        Add a new food from a template to today
    '''
    food = get_object_or_404(Food, id=food_id)
    if food.is_template:
        food_duplicate = copy(food)
        food_duplicate.pk = None  # don't overwrite existing food
        food_duplicate.is_template = False  # don't make multiple templates
        # update the date to today
        food_duplicate.day = get_or_create_day(
            request.user, request.POST['selected_date'])
        food_duplicate.save()
        return meal_update(request, food_duplicate.day)


def get_type_of_input(request):
    return render(request, 'calcounter/meal_type_input.html')


def get_auto_buttons(request):
    return render(request, 'calcounter/meal_auto_buttons.html')


def get_search_area(request):
    return render(request, 'calcounter/ingred_search_area.html')


def query_ingredient(request):
    query = request.POST['query']
    print(f"{query=}")
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


# USDA Nutrient ID Mapping (using common NDB numbers for accuracy)
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


def get_specific_usda_item(request, fdcId):
    single_url = f"https://api.nal.usda.gov/fdc/v1/food/{fdcId}?format=abridged&api_key={
        USDA_KEY}"
    item = requests.get(single_url).json()
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
            "name": "Total Calories",
            "value": (protein * 4) + (fat * 9) + (carbs * 4),
            "unit": "g"
        }
    # --- 2. Build the Final Output Dictionary ---
    final_data = {
        "fdc_id": fdcId,
        "name": item.get("description", "Unknown Food"),
        "macros": {},
        "minerals": {},
        "vitamins": {}
    }
    # Extract Macros and Target Minerals/Vitamins
    for id, value in all_nutrients.items():
        if id in VITAMIN:
            category = "vitamins"
        elif id in MINERAL:
            category = "minerals"
        elif id in MACRO:
            category = "macros"
        final_data[category][value["name"]] = value
    return render(request, 'calcounter/ingred.html', {'food': final_data})


# CRUD : Update a food


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


# Properly Display Meals

def calculate_totals(request):
    ''' Sum total nutrients for `selected_date` '''
    day = get_or_create_day(request.user, request.GET['selected_date'])
    foods = day.meals.all()
    totals = foods.aggregate(
        calories=Sum('calories'),
        protein=Sum('protein')
    )
    context = {
        "calories": totals['calories'] or 0,
        "protein": totals['protein'] or 0,
    }
    return render(request, "calcounter/totals.html", context)


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


def cancel_form(request):
    ''' Returns `entry_buttons` template '''
    return render(request, "calcounter/entry_buttons.html")
