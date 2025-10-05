"""
    Workouts manage 4 types:
    - Workouts Types    : Push, Pull, Legs, etc
    - Workouts          : Collection of lifts with a type on a day
    - Lifts             : name ('bench') & list of sets assigned to workout
    - Sets              : reps x weight belonging to a lift
"""
from django.shortcuts import render, HttpResponse, get_object_or_404
from django.db.models import F, Sum
from .models import Workout, WorkoutType, Lift, Set
from core.utils import get_or_create_today
from .forms import LiftForm, WTypeForm, SetForm
from random import randint


# get_x : returns list of x

def get_workouts(request):
    ''' returns a list of users workouts '''
    workouts = (
        Workout.objects.filter(day__user=request.user)
        .select_related("day", "workout_type")
        .prefetch_related("lifts__sets")
        .order_by("-day__date", "-id")
    )
    # handle event that user has an active workout ->
    context = {
        "workouts": workouts
    }
    return render(request, 'workouts/workout_list.html', context)


def get_workout_types(request):
    ''' returns list of workout types to start an active workout '''
    w_types = WorkoutType.objects.filter(user=request.user)
    return render(request,
                  'workouts/type_entry.html',
                  context={"workout_types": w_types})


def get_lifts(request, workout_id):
    ''' returns list of lifts for a particular workout '''
    workout = Workout.objects.get(pk=workout_id)
    lifts = workout.lifts.all()
    total = 0
    for lift in lifts:
        total += (Set.objects.filter(lift=lift)
                  .aggregate(total_volume=Sum(F("reps") * F("weight")))
                  )['total_volume'] or 0
    context = {
        "id": workout_id,
        "lifts": lifts,
        "total": int(total),
    }
    return render(request, 'workouts/lifts.html', context)


# CRUD : Adding new x

def add_workout(request, workout_type_id):
    '''
        Creates a Workout of workout_type for the current day
    '''
    day = get_or_create_today(request.user)
    workout_type = WorkoutType.objects.get(pk=workout_type_id)
    workout = Workout(day=day,
                      workout_type=workout_type,
                      is_active=True)
    workout.save()
    return render(request,
                  'workouts/active_workout.html',
                  context={"workout": workout})


def add_lift(request):
    '''
        POST: adds a lift to the current workout
        GET : returns entry form
    '''
    if request.POST:
        f = LiftForm(request.POST)
        if f.is_valid():
            cur_workout = Workout.objects.get(
                day__user=request.user, is_active=True)
            new_lift = f.save(commit=False)
            new_lift.workout = cur_workout
            new_lift.save()
            context = {
                "lift": new_lift,
                "set_form": SetForm()
            }
            return render(request, 'workouts/active_lift.html', context)
    form = LiftForm()
    return render(request, 'workouts/lift_entry.html', {"form": form})


def add_set(request, lift_id):
    '''
        POST: adds a set to the current lift, displays set
        GET : returns set entry
    '''
    lift = get_object_or_404(Lift,
                             pk=lift_id,
                             workout__day__user=request.user)
    if request.method == "POST":
        form = SetForm(request.POST)
        if form.is_valid():
            set_obj = form.save(commit=False)
            set_obj.lift = lift
            set_obj.save()
            # Return just the new row HTML
            return render(request,
                          "workouts/set_row.html",
                          {"set": set_obj}, status=201)
    # If GET or invalid POST, return blank form for user to try again
    form = SetForm()
    return render(request,
                  "workouts/set_entry.html",
                  {"form": form, "lift": lift})


# CRUD : Deleting / Ending active x

def end_lift(request, lift_id):
    '''
        appends lift to lift_list, blanks lift_entry
    '''
    lift = get_object_or_404(
        Lift, pk=lift_id, workout__day__user=request.user)
    return render(request, 'workouts/end_lift.html', {"lift": lift})


def delete_set(request, set_id):
    set = Set.objects.get(pk=set_id)
    set.delete()
    return HttpResponse("")


def end_workout(request):
    cur_workout = Workout.objects.get(is_active=True, day__user=request.user)
    cur_workout.is_active = False
    cur_workout.save()
    return render(request, 'workouts/workout_refresh.html')


def del_workout(request, workout_id):
    ''' deletes the workout '''
    workout = Workout.objects.get(pk=workout_id)
    workout.delete()
    return HttpResponse()


def back(request):
    ''' cancels the workout '''
    return render(request, 'workouts/start_workout.html')


# TODO: user can create new workout types, i.e. 'Upper'
# This used to be accessed with another button, but will move to
# the user's profile settings. This is currently functional but
# unable to be called from the client.

def add_workout_type(request):
    '''
        adds a new workout type template to the user
        POST: adds the template
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
            return get_workout_types(request)
        else:
            form = WTypeForm()
    else:
        form = WTypeForm()
    return render(request, 'workouts/new_type_entry.html', {"form": form})


def random_color():
    return "#{:06x}".format(randint(0, 0xFFFFFF))


def change_color(request):
    '''
        recieves color value to set workout type
        request contains:
        - workout_id
        - color
    '''
    workout = Workout.objects.get(pk=request.POST.get('workout_id'))
    workout.workout_type.color = request.POST.get('color')
    workout.workout_type.save()
    return get_workouts(request)
