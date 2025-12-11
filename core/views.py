from datetime import date
from random import randint
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .models import Day
from workouts.forms import WTypeForm
from workouts.models import WorkoutType
from .utils import get_or_create_day, get_or_create_today
from .forms import ProfileForm
from calcounter.models import Food
from workouts.models import Workout


def home(request):
    template = "core/base.html"
    return render(request, 'core/dashboard.html', {"template": template})


def index(request):
    return redirect('home/')

# === User Profile / Settings Screen ===


def auth_modal(request):
    return render(request, "core/auth_modal.html")


def close_profile(request):
    return render(request, "core/profile_nav.html")


def get_profile(request):
    return render(request, "core/profile.html")

# TODO: kinda jank


def update_timezone(request):
    profile = getattr(request.user, 'profile', None)
    form = ProfileForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        return get_profile(request)
    return render(request, "core/update_timezone.html", {"form": form})


def info_setting(request):
    return render(request, 'core/personal_info.html', {"user": request.user})


def theme_setting(request):
    return render(request, 'core/theme.html')


def food_setting(request):
    return render(request, 'core/food_settings.html')


def graph_setting(request):
    return render(request, 'core/graph_settings.html')


def workout_setting(request):
    types = request.user.workout_types.all()
    return render(request, 'core/workout_settings.html', {"workout_types": types})


def add_workout_type(request):
    '''
        POST: adds the type
        GET: returns entry form
    '''
    if request.POST:
        f = WTypeForm(request.POST)
        if f.is_valid():
            new_type = f.save(commit=False)
            new_type.user = request.user
            if new_type.color is None:
                new_type.color = random_color()
            new_type.save()
            types = request.user.workout_types.all()
            return render(request, 'core/workout_settings.html', {"workout_types": types})
    form = WTypeForm()
    return render(request, 'workouts/new_type_entry.html', {"form": form})


def edit_workout_type(request, type_id):
    ''' return prefilled form '''
    w_type = WorkoutType.objects.get(pk=type_id)
    if request.POST:
        f = WTypeForm(request.POST, instance=w_type)
        if f.is_valid():
            new_type = f.save()
            types = request.user.workout_types.all()
            return render(request, 'core/workout_settings.html', {"workout_types": types})
    form = WTypeForm(instance=w_type)
    return render(request, 'workouts/edit_type_entry.html', {"form": form, "type_id": type_id})


def del_workout_type(request, w_type):
    workout_t = WorkoutType.objects.get(pk=w_type)
    workout_t.delete()
    return workout_setting(request)


def random_color():
    return "#{:06x}".format(randint(0, 0xFFFFFF))


class HTMXLogoutView(LogoutView):
    next_page = reverse_lazy("core:home")

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        if request.headers.get("HX-Request") == "true":
            redirect = HttpResponse()
            redirect["HX-Redirect"] = "/"
            return redirect

        return response


class HTMXLoginView(LoginView):
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get("HX-Request") == "true":
            redirect_response = HttpResponse()
            redirect_response["HX-Redirect"] = self.get_success_url()
            return redirect_response
        return response


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # auto-login after sign up
            response = HttpResponse()
            response["HX-Redirect"] = "/"
            return response
    else:
        form = UserCreationForm()
    return render(request, 'core/signup.html', {'form': form})


# === Day Stuff ===

def get_bodyweight(request):
    '''
        Display user's bodyweight for the selected day
        if empty : show input
    '''
#    print(request.GET.get('selected_date'))
    day = get_or_create_day(request.user, request.GET.get('selected_date'))
    if day.bodyweight is None:
        print("no weight for the current day found")
        return render(request, 'core/bodyweight_input.html')
    else:
        print("weight already set")
        return render(request, 'core/bodyweight_update.html', context={"bodyweight": day.bodyweight})


def edit_bodyweight(request):
    day = get_or_create_day(request.user, request.GET.get('selected_date'))
    return render(request,
                  'core/bodyweight_input.html',
                  {"edit": True, "bw": day.bodyweight})


def add_bodyweight(request):
    day = get_or_create_day(request.user, request.POST.get('selected_date'))
    day.bodyweight = request.POST.get('weight')
    day.save()
    print(f"added new bodyweight: {request.POST.get('weight')}")
    return render(request, 'core/bodyweight_update.html', context={"bodyweight": day.bodyweight})


def display_today(request):
    day = get_or_create_today(request.user)
    return display_day(request, day.date)


def display_day(request, date):
    '''
        detailed day display to graph_display__container
    '''
    # need macros, tasks for day.html
    day = Day.objects.get(user=request.user, date=date)

    tasks = [
        {"name": "track weight", "done": True if day.bodyweight is not None else False},
        {"name": "track meal", "done": True if Food.objects.filter(
            day=day).exists() else False},
        {"name": "workout", "done": True if Workout.objects.filter(
            day=day).exists() else False},
        {"name": "hit macros", "done": True if day.calorie_ratio >= 1 else False},
    ]
    macros = [
        {"name": "calories", "amount": day.calories_consumed, "goal": day.calorie_goal},
        {"name": "protein", "amount": day.protein_consumed, "goal": day.protein_goal},
        {"name": "carbs", "amount": 0},
        {"name": "fats", "amount": 0},
    ]
    return render(request, 'core/day.html',
                  {"tasks": tasks, "macros": macros, "date": day.date})


# Task(name, done)
def daily_goals(request):
    day = get_or_create_today(request.user)
#    day = request.user.days.latest("date")
    tasks = [
        {"name": "track weight", "done": True if day.bodyweight is not None else False},
        {"name": "track meal", "done": True if Food.objects.filter(
            day=day).exists() else False},
        {"name": "workout", "done": True if Workout.objects.filter(
            day=day).exists() else False},
        {"name": "hit macros", "done": True if day.calorie_ratio >= 1 else False},
    ]
    return render(request, 'core/hud_tasks.html', {"tasks": tasks})


def default_hud(request):
    today = get_or_create_today(request.user)
    date = today.date.isoformat().split("T")[0]
    date_list = date.split("-")
    month = date_list[1]
    day = date_list[2]
    display_date = month + "/" + day
    editing_date = request.GET.get('selected_date')
    edit = False if (editing_date is None or date == editing_date) else True
    print(f"{date=}")
    print(f"{editing_date=}")
    print(f"{edit=}")
    context = {
        "date": display_date,
        "edit": edit,
        "editing_date": editing_date,
        "bw": today.bodyweight
    }

    return render(request, 'core/hud_default.html', context)


def calorie_hud(request):
    day = get_or_create_today(request.user)
#    day = request.user.days.latest("date")
    macros = [
        {"name": "calories", "amount": day.calories_consumed},
        {"name": "protein", "amount": day.protein_consumed},
        {"name": "carbs", "amount": 0},
        {"name": "fats", "amount": 0},
    ]
    return render(request, 'core/hud_cals.html', {"macro": macros})


def set_calorie_goal(request):
    pass


def set_protein_goal(request):
    pass
