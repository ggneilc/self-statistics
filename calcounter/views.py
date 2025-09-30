"""
    API for calorie counter
    get_food() -> returns list of consumed items

"""
from django.shortcuts import get_object_or_404, render, HttpResponse
from django.db.models import Sum
from .models import Food
from core.utils import get_or_create_day, get_or_create_today
from .forms import FoodForm

from copy import copy
from datetime import datetime


def get_food(request):
    ''' Returns `meal_list.html` with the `selected_date` '''
    if not request.user.is_authenticated:
        return HttpResponse("")
    day = get_or_create_day(request.user, request.GET['selected_date'])
    foods = Food.objects.filter(day=day)
    # dont allow saving foods that are already templates
    for food in foods:
        food.is_template = Food.objects.filter(
            name=food.name, is_template=True).exists()
    context = {"foods": foods}
    return render(request, "calcounter/meal_list.html", context)


def edit_food(request, food_id):
    food = get_object_or_404(Food, id=food_id)
    return render(request, 'calcounter/meal_edit.html', {"food": food})


def render_food(request, food_id):
    food = get_object_or_404(Food, id=food_id)
    food.is_template = Food.objects.filter(
        name=food.name, is_template=True).exists()
    return render(request, 'calcounter/meal.html', {
        "food": food,
        "just_updated": True})


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


def get_food_templates(request):
    ''' Returns `template_list.html` with `request.user` templates '''
    if not request.user.is_authenticated:
        return HttpResponse("")
    meals = Food.objects.filter(day__user=request.user)
    template_meals = [f for f in meals if f.is_template]
    if len(template_meals) == 0:      # if no templates, return entry form
        return add_food(request)
    context = {'foods': template_meals}
    return render(request, "calcounter/template_list.html", context)


def calculate_totals(request):
    ''' Sum total nutrients for `selected_date` '''
    if not request.user.is_authenticated:
        return HttpResponse("")
    day = get_or_create_day(request.user, request.GET['selected_date'])
    foods = Food.objects.filter(day=day)
    totals = foods.aggregate(
        calories=Sum('calories'),
        protein=Sum('protein')
    )
    context = {
        "calories": totals['calories'] or 0,
        "protein": totals['protein'] or 0,
    }
    return render(request, "calcounter/totals.html", context)


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
        return render(request, 'calcounter/meal_update.html', context)


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


def cancel_form(request):
    ''' Returns `entry_buttons` template '''
    return render(request, "calcounter/entry_buttons.html")

# TODO:
#  create method to delete all foods with date '0001-01-01'
#  and food.is_template = false


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
