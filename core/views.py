from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .models import Day

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
    template = "core/base_mobile.html" if is_mobile(request) else "core/base.html"
    return render(request, 'core/dashboard.html', {"template": template})

def index(request):
    return redirect('home/')

def auth_modal(request):
    return render(request, "core/auth_modal.html")


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

def get_bodyweight(request):
    '''
        Display user's bodyweight for the selected day
        if empty : show input
    '''
    print(request.GET.get('selected_date'))
    day = Day.objects.get(user=request.user, date=request.GET.get('selected_date'))
    if day.bodyweight is None:
        print("no weight for the current day found")
        return render(request, 'core/bodyweight_input.html')
    else:
        print("weight already set")
        return render(request, 'core/bodyweight_update.html', context={"bodyweight": day.bodyweight})

def add_bodyweight(request):
    day = Day.objects.get(user=request.user, date=request.POST.get('selected_date'))
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

def set_calorie_goal(request):
    pass

def set_protein_goal(request):
    pass