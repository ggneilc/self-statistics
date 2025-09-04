from django.shortcuts import get_object_or_404, render, HttpResponse
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from .models import Food
from core.models import Day
from .forms import FoodForm

from copy import copy
from datetime import datetime


def get_food(request):
    '''
        Display the meals for the day
    '''
    if not request.user.is_authenticated:
        return HttpResponse("")
    
    if request.POST:
        tmp = request.POST.get('selected_date')
    else:
        tmp = request.GET.get('selected_date')

    date = tmp if tmp is not None else datetime.today().date()

    day, _ = Day.objects.get_or_create(user=request.user, date=date)
    foods = Food.objects.filter(date=date, user=request.user)
    totals = foods.aggregate(
        calories=Sum('calories'),
        protein=Sum('protein')
    )
    
    context = {
        "date": date,
        "foods": foods,
        "calories": totals['calories'] or 0,
        "protein": totals['protein'] or 0,
        "bodyweight": day.bodyweight or None
        }
    return render(request, "calcounter/meal_list.html", context)

def get_food_templates(request):
    ''' Return list of meal templates'''
    if not request.user.is_authenticated:
        return HttpResponse("<div> Login </div>")
    meals = Food.objects.filter(user=request.user).order_by('name')
    template_meals = [f for f in meals if f.is_template]
    return render(request, "calcounter/template_list.html", {'foods': template_meals})

def calculate_totals(request, date=None):
    '''
        Sum total nutrients for given day.
        Defaults to today if no date given in args or request
    '''
    if not request.user.is_authenticated:
        return HttpResponse("<div> Login </div>")
    if request.POST:
        day = request.POST['day']
    elif date:
        day = date
    else:
        day = datetime.today().date()

    foods = Food.objects.filter(date=day, user=request.user)
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
            if request.POST['action'] == 'save_template':
                new_food.is_template = True
            new_food.save()
            return render(request, 'calcounter/meal_refresh.html')
    else:
        form = FoodForm(initial={"date": request.GET.get('selected_date')})
    return render(request, "calcounter/meal_entry.html", {"form": form})

def add_food_template(request, food_id):
    '''
        Add a new food from a template to today
    '''
    food = get_object_or_404(Food, id=food_id)
    if food.is_template:
        food_duplicate = copy(food)
        food_duplicate.pk = None  # don't overwrite existing food
        food_duplicate.is_template = False  # don't make multiple templates
        food_duplicate.date = str(datetime.today().date())  # update the date to today
        food_duplicate.save()
        return get_food(request)
        
def cancel_form(request):
    '''
        Returns entry buttons template
    '''
    return render(request, "calcounter/entry_buttons.html")

def delete_food(request, food_id):
    '''
        Delete food entry:
        - todo: find way to keep date selected
    '''
    food = get_object_or_404(Food, id=food_id)
    # If you just created a new template & deleted it from that day, 
    # Don't actually delete the template. TODO: create method to delete
    # all foods with date '0001-01-01'
    if food.is_template:
        food.date = datetime(1,1,1)
        food.save()
        return calculate_totals(request)
    food.delete()

    return calculate_totals(request, date=food.date)

def delete_food_template(request, food_id):
    '''
        Delete a saved food template
    '''
    food = get_object_or_404(Food, id=food_id)
    food.is_template = False
    food.save()
    return HttpResponse("")