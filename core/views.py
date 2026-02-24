from datetime import date, timedelta
from random import randint
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy, reverse
from django.contrib.auth import login
from django.http import JsonResponse, FileResponse
from django.conf import settings
import os
from django.contrib.auth.forms import UserCreationForm
from .models import Day
from workouts.forms import WTypeForm
from workouts.models import WorkoutType
from .utils import get_or_create_day, get_or_create_today
from .forms import ProfileForm
from calcounter.models import Food
from workouts.models import Workout


def home(request):
    return render(request, 'core/base.html')


def index(request):
    return redirect('home/')


def manifest_view(request):
    """Web App Manifest for PWA / Add to Home Screen (standalone, no browser UI)."""
    base = request.build_absolute_uri("/").rstrip("/")
    # Chrome requires at least one icon that is 192x192 or larger for installability
    icons = [
        {
            "src": request.build_absolute_uri("/static/core/favicon_32x32.png"),
            "sizes": "32x32",
            "type": "image/png",
            "purpose": "any",
        },
    ]
    
    # Add larger icons if they exist (required for Chrome installability)
    import os
    from django.conf import settings
    static_base = os.path.join(settings.BASE_DIR, 'core', 'static', 'core')
    
    if os.path.exists(os.path.join(static_base, 'icon_192x192.png')):
        icons.append({
            "src": request.build_absolute_uri("/static/core/icon_192x192.png"),
            "sizes": "192x192",
            "type": "image/png",
            "purpose": "any maskable",
        })
    
    if os.path.exists(os.path.join(static_base, 'icon_512x512.png')):
        icons.append({
            "src": request.build_absolute_uri("/static/core/icon_512x512.png"),
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "any maskable",
        })
    
    manifest = {
        "name": "Self Stats",
        "short_name": "Self Stats",
        "description": "Personal analytics, nutrition, and workouts",
        "start_url": base + reverse("core:home"),
        "display": "standalone",
        "orientation": "portrait",
        "scope": base + "/",
        "theme_color": "#1a1a1a",
        "background_color": "#121212",
        "icons": icons,
    }
    response = JsonResponse(manifest)
    response["Content-Type"] = "application/manifest+json"
    return response


def service_worker_view(request):
    """Serve service worker from root so it can control the entire site."""
    sw_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'core', 'js', 'sw.js')
    if os.path.exists(sw_path):
        response = FileResponse(open(sw_path, 'rb'), content_type='application/javascript')
        response['Service-Worker-Allowed'] = '/'  # Allow controlling entire site
        return response
    return HttpResponse('Service worker not found', status=404)


# === User Profile / Settings Screen ===


def auth_modal(request):
    return render(request, "core/auth_modal.html")


def close_profile(request):
    return HttpResponse("")


def get_profile(request):
    return render(request, "core/profile.html")

# TODO: kinda jank


def update_timezone(request):
    profile = getattr(request.user, 'profile', None)
    form = ProfileForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        response = get_profile(request)
        response['HX-Trigger'] = 'profileSaved'
        return response
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
            response = render(request, 'core/workout_settings.html', {"workout_types": types})
            response['HX-Trigger'] = 'workoutTypeCreated'
            return response
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
            response = render(request, 'core/workout_settings.html', {"workout_types": types})
            response['HX-Trigger'] = 'workoutTypeUpdated'
            return response
    form = WTypeForm(instance=w_type)
    return render(request, 'workouts/edit_type_entry.html', {"form": form, "type_id": type_id})


def del_workout_type(request, w_type):
    workout_t = WorkoutType.objects.get(pk=w_type)
    workout_t.delete()
    types = request.user.workout_types.all()
    response = render(request, 'core/workout_settings.html', {"workout_types": types})
    response['HX-Trigger'] = 'workoutTypeDeleted'
    return response


def random_color():
    return "#{:06x}".format(randint(0, 0xFFFFFF))

# === Navbar Pages ===


def dashboard_page(request):
    return render(request, 'core/dashboard.html')


def workout_page(request):
    return render(request, 'core/workout_dashboard.html')


def nutrition_page(request):
    return render(request, 'core/nutrition_dashboard.html')

# === Authentication Pages ===


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

def get_current_streak(request):
    today = date.today()
    streak = 0
    curr = today

    while request.user.days.filter(date=curr).exists():
        streak += 1
        curr -= timedelta(days=1)

    return render(request, "core/streak_highlight.html", {"streak": streak})


def get_water(request):
    """Return water input form (for modal)."""
    return render(request, 'core/water_input.html')


# TODO: update to return an animation of water filling the input,
# then return to input : (no display, macro-chart shows data)
def add_water(request):
    date = request.POST.get('selected_date')
    day = get_or_create_day(user=request.user, selected_date=date)
    water = request.POST.get('water')
    if water:
        day.water_consumed += float(water)
        day.save()
        print(f"added new water: {water}L")
    return render(request, 'core/water_input.html')


def get_sleep(request):
    date = request.GET.get('selected_date')
    day = get_or_create_day(user=request.user, selected_date=date)
    if day.sleep == 0:
        print("no sleep for the current day found")
        return render(request, 'core/sleep_input.html')
    else:
        print("sleep already set")
        return render(request, 'core/sleep_update.html', context={"sleep": day.sleep})

def edit_sleep(request):
    date = request.GET.get('selected_date')
    day = get_or_create_day(user=request.user, selected_date=date)
    return render(request,
                  'core/sleep_input.html',
                  {"edit": True, "sleep": day.sleep})


def add_sleep(request):
    date = request.POST.get('selected_date')
    day = get_or_create_day(user=request.user, selected_date=date)
    sleep = request.POST.get('sleep')
    day.sleep = sleep
    day.save()
    print(f"added new sleep: {request.POST.get('sleep')}")
    return render(request, 'core/sleep_update.html', context={"sleep": sleep})

def get_bodyweight(request):
    '''
        Display user's bodyweight for the selected day
        if empty : show input
    '''
    date = request.GET.get('selected_date')
    day = get_or_create_day(user=request.user, selected_date=date)
    if day.bodyweight is None:
        print("no weight for the current day found")
        return render(request, 'core/bodyweight_input.html')
    else:
        print("weight already set")
        return render(request, 'core/bodyweight_update.html', context={"bodyweight": day.bodyweight})


def edit_bodyweight(request):
    date = request.GET.get('selected_date')
    day = get_or_create_day(user=request.user, selected_date=date)
    return render(request,
                  'core/bodyweight_input.html',
                  {"edit": True, "bw": day.bodyweight})


def add_bodyweight(request):
    date = request.POST.get('selected_date')
    day = get_or_create_day(user=request.user, selected_date=date)
    bw = request.POST.get('weight')
    day.bodyweight = bw
    day.save()
    print(f"added new bodyweight: {request.POST.get('weight')}")
    return render(request, 'core/bodyweight_update.html', context={"bodyweight": bw})


def display_today(request):
    day = get_or_create_today(request.user)
    return display_day(request, day.date)


def display_day(request, date):
    '''
        detailed day display to graph_display__container
        - creates day if not exists
    '''
    day = get_or_create_day(user=request.user, selected_date=date)
    response = render(request, 'core/day.html', {"day": day})
    response['HX-Trigger'] = 'dayUpdated' # This is our custom signal
    return response
    


# Task(name, done)
def daily_goals(request):
    day = get_or_create_today(request.user)
#    day = request.user.days.latest("date")
    tasks = [
        {"name": "track weight", "done": True if day.bodyweight is not None else False},
        {"name": "track meal", "done": True},
        {"name": "workout", "done": True if Workout.objects.filter(
            day=day).exists() else False},
        {"name": "hit macros", "done": True if day.calorie_ratio >= 1 else False},
    ]
    return render(request, 'core/hud_tasks.html', {"tasks": tasks})


def get_macro_goal(request):
    day = get_or_create_today(request.user)
    context = {
        "cals": day.calorie_goal,
        "pro": day.protein_goal
    }
    return render(request, 'core/macro_highlight.html', context)


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
