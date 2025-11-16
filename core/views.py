from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .models import Day
from .utils import get_or_create_day
from .forms import ProfileForm
from calcounter.models import Food
from workouts.models import Workout


# MOBILE SPECIFICS

def is_mobile(request):
    ua = request.META.get('HTTP_USER_AGENT', '').lower()
    return 'mobile' in ua and 'tablet' not in ua


def get_meal_column(request):
    return render(request, "core/column_meal.html")


def get_graph_column(request):
    return render(request, "core/column_graph.html")


def get_lift_column(request):
    return render(request, "core/column_lift.html")

# END MOBILE


def home(request):
    template = "core/base_mobile.html" if is_mobile(
        request) else "core/base.html"
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

#TODO: kinda jank
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
    print(request.GET.get('selected_date'))
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


def display_day(request, date):
    '''
        detailed day display to graph_display__container
    '''
    print("displaying day")
    day = Day.objects.get(user=request.user, pk=date)
    return render(request, 'core/day.html', {"day": day})


def daily_goals(request):
    day = get_or_create_day(request.user, request.GET.get('selected_date'))
    day.entered_bodyweight = True if day.bodyweight is not None else False
    day.entered_meal = True if Food.objects.filter(day=day).exists() else False
    day.did_workout = True if Workout.objects.filter(
        day=day).exists() else False
    return render(request, 'core/tasks.html', {"day": day})


def set_calorie_goal(request):
    pass


def set_protein_goal(request):
    pass
