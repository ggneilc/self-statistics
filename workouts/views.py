"""
    Workouts manage 6 types:
    - Workout Types     : Push, Pull, Legs, etc
    - Workouts          : Collection of lifts with a type on a day
    - Lifts             : name ('bench') & list of sets assigned to workout
    - Sets              : reps x weight belonging to a lift (set_row.html)
    - Movement Library  : Global library of movements 
    - Movement          : defines a type of lift 
    - Weekly Volume     : Weekly volume of sets performed 
"""
from django.shortcuts import render,  get_object_or_404
from django.http import HttpResponse, HttpRequest
from django.template.loader import render_to_string
from .models import (
    Workout,
    WorkoutType,
    Lift,
    Set,
    WeeklyVolume,
    Movement,
    MovementLibrary,
    BODYPARTS,
    LIFT_TYPES
)
from core.utils import get_or_create_day
from .forms import SetForm, MovementForm
#from copy import copy
from datetime import datetime, timezone, timedelta
from django.db.models import Q, F, Sum

bodypart_map = dict(BODYPARTS)

# --- C_R_UD : get_X

def get_workouts(request: HttpRequest,
                 mode: str = 'history') -> HttpResponse:
    ''' workouts for a user (workout history) '''
    # Check if user has an active workout
    active_workout = Workout.objects.filter(day__user=request.user, is_active=True).first()
    if active_workout:
        # Render a different view for the active workout
        return render(request, 'workouts/active_workout.html', {"workout": active_workout, "active_workout": True})

    else:
        workouts = Workout.objects.filter(day__user=request.user).annotate(
            total_vol=Sum(F('lifts__sets__weight') * F('lifts__sets__reps'))
        ).select_related("day", "workout_type").order_by("-day__date")
        return render(request, 'workouts/workout_list.html', {"workouts": workouts, "active_workout": False})

def get_workout(request: HttpRequest, workout_id: int) -> HttpResponse:
    ''' returns a specific workout (inspected workout) '''
    workout = get_object_or_404(Workout, pk=workout_id, day__user=request.user)
    return render(request, 'workouts/workout_details.html', {"workout": workout})

def get_movements(request: HttpRequest) -> HttpResponse:
    '''
    Returns a list of movements available to a user
    :param bodypart -> filter by specific bodypart
    :param category -> filter by specific category
    :param global_m -> filter all movement or specific to user
    '''
    bodypart = request.GET.get('bodypart')
    category = request.GET.get('category')   
    wtype_id = request.GET.get('wtype')   
    url_name = request.resolver_match.url_name
    print(f"{bodypart=} | {category=} | {url_name=} | {wtype_id=}")
    queryset = MovementLibrary.objects.filter(
        is_premium=False) if url_name == 'movements_global' else Movement.objects.filter(
            user=request.user, is_archived=False)
    filters = Q()
    if wtype_id:
        wtype = get_object_or_404(WorkoutType, pk=wtype_id)
        allowed_codes = wtype.target_muscles.values_list('bodypart', flat=True)
        filters &= Q(bodypart__in=allowed_codes)
    if bodypart:
        filters &= Q(bodypart=bodypart)
    if category:
        filters &= Q(category=category)
    mvments = queryset.filter(filters).distinct()
    if url_name == 'movements_global':  # movement modal
        mode = "select"
    elif url_name == 'movements_active':  # active workout
        mode = "active"
    else:  # lift overview
        mode = "view"
    context = {
        "movements": mvments,
        "mode": mode
    }
    return render(request, 'workouts/movements.html', context)

def get_movement(request: HttpRequest, movement_id: int) -> HttpResponse:
    ''' specific movement overview'''
    mvment = Movement.objects.get(pk=movement_id)
    return render(request, 'workouts/movement_details.html', {"movement": mvment})

# TODO
def get_lifts(request: HttpRequest, movement_id: int) -> HttpResponse:
    ''' lifts for selected movement (movement details) '''
    pass

def get_wtypes(request: HttpRequest) -> HttpResponse:
    ''' workout types for a user '''
    url_name = request.resolver_match.url_name
    context = {
        "wtypes": request.user.workout_types.all(),
        "mode": 'dash' if url_name == 'workout_types' else 'active'
    }
    return render(request, "workouts/workout_types.html", context) 

def get_weekly_sets(request: HttpRequest, workout_id: int | None = None) -> HttpResponse:
    ''' sets performed per muscle group this week '''
    date = request.GET['selected_date']
    today = datetime.strptime(date, "%Y-%m-%d").date()
    print(f"{today=}")
    this_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
    # Get the user's goal
    goal = request.user.profile.weekly_set_goal
    # Get volumes from our WeeklyVolume model
    volumes = WeeklyVolume.objects.filter(user=request.user, start_date=this_sunday)
    stats = []
    # Loop through your BODYPARTS constant to ensure all muscles show up
    # aggregate shoulder
    for code, name in BODYPARTS:
        # Find the count for this specific muscle
        volume_entry = volumes.filter(muscle_group=code).first()
        count = volume_entry.set_count if volume_entry else 0
        
        # Calculate percentage (capped at 100% for the bar height)
        percent = min((count / goal) * 100, 100) if goal > 0 else 0
        print(f"{percent=} for {name=}")
        stats.append({
            'name': name,
            'count': count,
            'percent': percent,
            'is_complete': count >= goal
        })
    ctx = {
        'stats': stats,
        'goal': goal,
        'date': this_sunday
    }
    if workout_id:
        ctx['delete_workout'] = True
        ctx['workout_id'] = workout_id
    return render(request, 'workouts/weekly_sets.html', ctx)

def get_bodyparts(request: HttpRequest,
                  wtype_id: int | None = None) -> HttpResponse:
    ''' list of bodyparts, can be filtered by wtype_id '''
    if wtype_id:
        wtype = get_object_or_404(WorkoutType, pk=wtype_id, user=request.user)
        codes = wtype.target_muscles.values_list('bodypart', flat=True)
        bodyparts = [(code, bodypart_map[code]) for code in codes if code in bodypart_map]
    else:
        bodyparts = BODYPARTS
    return render(request, 'workouts/bodypart_chips.html', {"bodyparts": bodyparts, "active": False})

def get_categories(request: HttpRequest) -> HttpResponse:
    ''' list of all categories '''
    url_name = request.resolver_match.url_name
    active = url_name == 'categories_active'
    return render(request, 'workouts/machines.html', {"categories": LIFT_TYPES, "active": active})

# --- _C_RUD : add_X

def add_workout(request: HttpRequest, wtype_id: int) -> HttpResponse:
    ''' add new workout to today with wtype '''
    wtype = get_object_or_404(WorkoutType, pk=wtype_id, user=request.user)
    workout = Workout.objects.create(
        day=get_or_create_day(request.user, request.POST.get('selected_date')),
        workout_type=wtype,
        start_time=datetime.now().time(),
        is_active=True
    )
    bodyparts = workout.bodypart_list()
    return render(request, 'workouts/active_workout.html', {"workout": workout, "bodyparts": bodyparts})

def add_movement(request: HttpRequest,
                 mv_id: int | None = None) -> HttpResponse:
    ''' user registers movement '''
    url_name = request.resolver_match.url_name
    print(f"{url_name=}")
    if url_name == 'start':
        # return movement modal to start the register process
        return render(request, "workouts/movement_modal.html")
    elif url_name == 'add_mv':
        # add the movement from global library to user 
        # -> refresh their dashboard
        # check if user already has this movement
        if Movement.objects.filter(user=request.user, base_movement__pk=mv_id).exists():
            return get_movements(request)
        movement = MovementLibrary.objects.get(pk=mv_id)
        Movement.objects.create(
            user=request.user,
            base_movement=movement,
            name=movement.name,
            bodypart=movement.bodypart,
            category=movement.category
        )
        return get_movements(request)
    elif url_name == 'add_custom_mv':
        form = MovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            movement.user = request.user
            movement.save()
            return get_movements(request)
    elif url_name == 'mv_form':
        bodypart = request.GET.get('bodypart')
        category = request.GET.get('category')   
        print(f"found filters {bodypart=} | {category=}")
        bodypart_name = bodypart_map.get(bodypart) if bodypart is not None else ''
        form = MovementForm(initial={
            'bodypart': bodypart,
            'category': category
        })
        context = {
            "form": form,
            "is_filtered_bp": bool(bodypart),
            "is_filtered_cat": bool(category),
            "bodypart_name": bodypart_name
        }
        return render(request, 'workouts/movement_form.html', context)

def add_lift(request: HttpRequest, movement_id: int) -> HttpResponse:
    ''' instantiate a movement for current workout '''
    movement = get_object_or_404(Movement, pk=movement_id, user=request.user)
    workout = Workout.objects.get(day__user=request.user, is_active=True)
    lift = Lift.objects.create(
        workout=workout,
        movement=movement
    )
    form = SetForm()
    # return the active lift
    return render(request, 'workouts/active_lift.html', {"lift": lift, "editing": False, "set_form": form})

def add_set(request: HttpRequest, lift_id: int) -> HttpResponse:
    ''' add a set to current lift '''
    lift = get_object_or_404(Lift, pk=lift_id, workout__day__user=request.user)
    if request.method == "POST":
        form = SetForm(request.POST)
        if form.is_valid():
            set_obj = form.save(commit=False)
            set_obj.lift = lift
            set_obj.save()
            return render(request,
                          "workouts/set_row.html",
                          {"set": set_obj})
    form = SetForm()
    return render(request,
                  "workouts/set_entry.html",
                  {"form": form, "lift": lift, "editing": False})

def add_wtype(request: HttpRequest) -> HttpResponse:
    ''' add a new workout type '''
    pass


# --- CR_U_D : edit_X

def edit_movement(request: HttpRequest, movement_id: int) -> HttpResponse:
    ''' edit movement info (name/bodypart)'''
    pass

def edit_lift(request: HttpRequest, lift_id: int) -> HttpResponse:
    ''' reopens lift to edit '''
    lift = get_object_or_404(Lift, pk=lift_id, workout__day__user=request.user)
    previous_sets = lift.sets.all()
    set_forms = []
    for s in previous_sets:
        set_forms.append(SetForm(instance=s))
    return render(request, 'workouts/active_lift.html', {"lift": lift, "set_forms": set_forms, "editing": True})

def edit_set(request: HttpRequest, set_id: int) -> HttpResponse:
    ''' turns set_row to set_form '''
    set = get_object_or_404(Set, pk=set_id, lift__workout__day__user=request.user)
    if request.method == "POST":
        form = SetForm(request.POST, instance=set)
        if form.is_valid():
            set = form.save()
            return render(request, "workouts/set_row.html", {"set": set})
    else:
        form = SetForm(instance=set)
        return render(request, 'workouts/set_entry.html', {"form": form, "set": set, "editing": True})

def edit_wtype(request: HttpRequest, type_id: int) -> HttpResponse:
    ''' edit type name/color/bodyparts '''
    pass

def change_color(request: HttpRequest) -> HttpResponse:
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


# --- CRU_D_ : delete_X , if data exists; archive

def delete_workout(request: HttpRequest, workout_id: int) -> HttpResponse:
    workout = get_object_or_404(Workout, pk=workout_id, day__user=request.user)
    workout.delete()
    return get_weekly_sets(request, workout_id)

def delete_movement(request: HttpRequest, movement_id: int) -> HttpResponse:
    ''' if no lifts, delete movement, otherwise archive '''
    movement = get_object_or_404(Movement, pk=movement_id, user=request.user)
    if movement.instances.count() == 0:
        movement.delete()
    else:
        movement.is_archived = True
        movement.save()
    return get_movements(request)

def delete_lift(request: HttpRequest, lift_id: int) -> HttpResponse:
    pass

def delete_set(request: HttpRequest, set_id: int) -> HttpResponse:
    set = get_object_or_404(Set, pk=set_id, lift__workout__day__user=request.user)
    set.delete()
    return clear(request)

def delete_wtype(request: HttpRequest, type_id: int) -> HttpResponse:
    pass


# --- Active Workout Interactions

def wtype_selection(request: HttpRequest) -> HttpResponse:
    ''' returns `type_entry.html` for user to choose this workout's type ''' 
    wtypes = request.user.workout_types.all()
    return render(request, 'workouts/type_entry.html', {"workout_types": wtypes})


def end_workout(request: HttpRequest, workout_id: int) -> HttpResponse:
    ''' end the active workout '''
    workout = get_object_or_404(Workout, pk=workout_id, day__user=request.user, is_active=True)
    workout.is_active = False
    workout.end_time = datetime.now().time()
    workout.save()
    return render(request, 'workouts/workout_history.html')


def end_lift(request: HttpRequest, lift_id: int) -> HttpResponse:
    ''' end the active lift : if no sets, delete lift '''
    lift = get_object_or_404(Lift, pk=lift_id, workout__day__user=request.user)
    if lift.sets.count() == 0:
        lift.delete()
    workout = Workout.objects.get(day__user=request.user, is_active=True)
    bodyparts = workout.bodypart_list()
    return render(request, 'workouts/active_lift_selection.html', {"workout": workout, "bodyparts": bodyparts})

# --- Load Areas / Helpers

def clear(request: HttpRequest) -> HttpResponse:
    return HttpResponse('')

