from django.shortcuts import render, HttpResponse, get_object_or_404
from django.db.models import F, Sum
from .models import Workout, WorkoutType, Lift, Set
from core.utils import get_or_create_day, get_or_create_today
from .forms import LiftForm, WTypeForm, SetForm
from datetime import datetime
from random import randint


def get_workouts(request):
    ''' returns a list of users workouts '''
    workouts = (
        Workout.objects.filter(day__user=request.user)
        .select_related("day", "workout_type")
        .prefetch_related("lifts__sets")
        .order_by("-day__date", "-id")
    )
    context = {
        "workouts": workouts
    }
    return render(request, 'workouts/workout_list.html', context)


def get_lifts(request, workout_id):
    ''''''
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


def add_workout(request, workout_type_id):
    ''' opens a workout for the day to add lifts to  '''
    day = get_or_create_today(request.user)
    workout_type = WorkoutType.objects.get(pk=workout_type_id)
    workout = Workout(day=day,
                      workout_type=workout_type,
                      is_active=True)
    workout.save()
    return show_active_workout(request)


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


def add_set_dep(request, lift_id):
    '''
        POST: adds a set to the current lift
        GET : returns set entry
    '''
    if request.POST:
        s = SetForm(request.POST)
        if s.is_valid():
            new_set = s.save(commit=False)
            new_set.lift = Lift.objects.get(pk=lift_id)
            new_set.save()
            return HttpResponse("")
        else:
            form = SetForm()
    else:
        form = SetForm()
    context = {
        "form": form,
        "lift_id": lift_id
    }
    return render(request, 'workouts/set_entry.html', context)


def add_set(request, lift_id):
    lift = get_object_or_404(Lift, pk=lift_id, workout__day__user=request.user)

    if request.method == "POST":
        form = SetForm(request.POST)
        if form.is_valid():
            set_obj = form.save(commit=False)
            set_obj.lift = lift
            set_obj.save()
            # Return just the new row HTML
            return render(request, "workouts/set_row.html",
                          {"set": set_obj}, status=201)
    # If GET or invalid POST, return blank form for user to try again
    form = SetForm()
    return render(request, "workouts/set_entry.html",
                  {"form": form, "lift": lift})


def end_lift(request, lift_id):
    ''' appends lift to lift_list, blanks lift_entry '''
    lift = get_object_or_404(Lift, pk=lift_id, workout__day__user=request.user)
    return render(request, 'workouts/end_lift.html', {"lift": lift})


def delete_set(request, set_id):
    set = Set.objects.get(pk=set_id)
    set.delete()
    return HttpResponse("")


def end_workout(request):
    ''' closes current workout '''
    cur_workout = Workout.objects.get(is_active=True, day__user=request.user)
    cur_workout.is_active = False
    cur_workout.save()
    return render(request, 'workouts/workout_refresh.html')


def get_active_workout(request):
    ''' return active workout '''
    if has_active_workout(request.user):
        return show_active_workout(request)
    else:
        return HttpResponse(404)


def load_workout_entry(request):
    '''
    check if user has active workout:
        true:
            no type set:  display push/pull/legs
            has type set: display add_lift
        false: display 'no workout'
    '''
    if has_active_workout(request.user):
        workout = Workout.objects.get(user=request.user, is_active=True)
        if has_type_set(workout):
            return add_lift(request)
        else:
            return get_workout_types(request)
    else:
        return render(request, 'workouts/start_workout.html')


def set_workout_type(request, workout_type_id):
    '''
        sets the active workout's type and displays add_lift
    '''
    workout = Workout.objects.get(user=request.user, is_active=True)
    workout_type = WorkoutType.objects.get(pk=workout_type_id)
    workout.workout_type = workout_type
    workout.save()
    return render(request, 'workouts/active_workout.html', context={"workout": workout})


def show_active_workout(request):
    day = get_or_create_today(request.user)
    workout = Workout.objects.get(day=day, is_active=True)
    return render(request, 'workouts/active_workout.html', context={"workout": workout})


def del_workout(request, workout_id):
    ''' deletes the workout '''
    workout = Workout.objects.get(pk=workout_id)
    workout.delete()
    return HttpResponse()


def back(request):
    ''' cancels the workout '''
    return render(request, 'workouts/start_workout.html')


def get_workout_types(request):
    '''
        returns list of workout types to assign an active workout
    '''
    w_types = WorkoutType.objects.filter(user=request.user)
    return render(request, 'workouts/type_entry.html', context={"workout_types": w_types})


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
            return load_workout_entry(request)
        else:
            form = WTypeForm()
    else:
        form = WTypeForm()
    return render(request, 'workouts/new_type_entry.html', {"form": form})


def has_active_workout(user):
    try:
        day = get_or_create_today(user)
        is_active = Workout.objects.filter(day=day, is_active=True)[0]
        return is_active  # , True  # bool flag
    except IndexError:
        return False


def has_type_set(workout):
    return True if workout.workout_type is not None else False


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
