"""
    Workouts manage 4 types:
    - Workouts Types    : Push, Pull, Legs, etc
    - Workouts          : Collection of lifts with a type on a day
    - Lifts             : name ('bench') & list of sets assigned to workout
    - Sets              : reps x weight belonging to a lift
"""
from django.shortcuts import render, HttpResponse, get_object_or_404
from django.template.loader import render_to_string
from .models import Workout, WorkoutType, Lift, Set, WeeklyVolume, BODYPARTS, LIFT_TYPES
from core.utils import get_or_create_day
from .forms import LiftForm, SetForm
from copy import copy
from datetime import datetime, timezone, timedelta
from django.db.models import Q


# get_x : returns list of x

# --- Workout History
def get_workouts(request):
    ''' returns a list of users workouts '''
    workouts = (
        Workout.objects.filter(day__user=request.user)
        .select_related("day", "workout_type")
        .prefetch_related("lifts__sets")
        .order_by("-day__date", "-id")
    )
    # add total volume to each workout
    for w in workouts:
        w.total = int(w.total_volume())
    # TODO: handle event that user has an active workout -> return active workout
    context = {
        "workouts": workouts
    }
    return render(request, 'workouts/workout_list.html', context)


def get_workout_types(request):
    ''' returns list of workout types to start an active workout '''
    url_name = request.resolver_match.url_name
    w_types = WorkoutType.objects.filter(user=request.user)
    if url_name == "load_entry":
        return render(request,
                  'workouts/type_entry.html',
                  context={"workout_types": w_types})
    else:
        return render(request,
                  'workouts/type_select.html',
                  context={"workout_types": w_types})


def get_lifts(request, workout_id):
    ''' returns list of lifts for a particular workout '''
    workout = Workout.objects.get(pk=workout_id)
    lifts = workout.lifts.all()
    total = workout.total_volume()
    context = {
        "id": workout_id,
        "lifts": lifts,
        "total": int(total),
    }
    return render(request, 'workouts/lifts.html', context)

# --- Active Workout


# TODO: un-hard-code this to allow users to categorize how they want
def filterBodyparts(request, workout_type):
    if (workout_type.name == 'Push'):
        return ('Chest', 'Tricep', 'Shoulder')
    elif (workout_type.name == 'Pull'):
        return ('Bicep', 'Trap', 'Lat')
    elif (workout_type.name == 'Legs'):
        return ('Quadricep', 'Hamstring', 'Calf', 'Ad/Abductor')
    else:
        form = LiftForm()
        return render(request, 'workouts/lift_entry.html', {"form": form})


def get_bodyparts(request, workout_type_id):
    workout_type = WorkoutType.objects.get(pk=workout_type_id)
    bodyparts = filterBodyparts(request, workout_type)
    url_name = request.resolver_match.url_name
    if url_name == 'bpb':
        ctx = {'bodyparts': bodyparts, 'in_overview': False}
    else:
        ctx = {'bodyparts': bodyparts, 'in_overview': True}
    return render(request, 'workouts/bodypart_buttons.html', ctx)

def get_machines(request):
    bodypart = request.GET.get("bodypart")
    url_name = request.resolver_match.url_name
    ctx = {
        'machines': ('Machine', 'Cable', 'Barbell', 'Dumbbell'),
        'bodypart': bodypart,
    }
    if url_name == 'machines':
        ctx['in_overview'] = False
    else:
        ctx['in_overview'] = True
    return render(request, 'workouts/machines.html', ctx)


LIFT_TYPES_MAP = {label: code for code, label in LIFT_TYPES}
BODYPARTS_MAP = {label: code for code, label in BODYPARTS}


def get_lift_templates(request):
    bodypart = request.GET.get("bodypart")
    machine = request.GET.get("machine")
    bp_code = BODYPARTS_MAP.get(bodypart)
    lift_code = LIFT_TYPES_MAP.get(machine)
    lifts = Lift.objects.filter(bodypart=bp_code,
                                lift_type=lift_code,
                                is_template=True)
    context = {
        "lifts": lifts,
        "machine": lift_code,
        "bodypart": bp_code
    }
    return render(request, 'workouts/lift_templates.html', context)


# TODO: this function is literally get_lifts(), DRY
def get_active_lift_list(request, workout_id):
    workout = Workout.objects.get(pk=workout_id)
    lifts = workout.lifts.all()
    total = workout.total_volume()
    context = {
        "active": True,
        "id": workout_id,
        "lifts": lifts,
        "total": int(total),
    }
    return render(request, "workouts/lifts.html", context)

# --- Inspecting Lift


def get_lift_details(request, lift_id):
    '''inspecting lift in workout history'''
    lift = Lift.objects.get(pk=lift_id)
    workout = lift.workout
    # determine if there exists a template of a left -> don't allow user to save
    lift.is_template = Lift.objects.filter(workout__day__user=request.user,
                                           exercise_name=lift.exercise_name, is_template=True).exists()
    return render(request, 'workouts/lift_details.html', {"lift": lift, "workout": workout})


def get_workout_details(request, workout_id):
    '''workout to remain expanded'''
    workout = Workout.objects.get(pk=workout_id)
    workout.total = int(workout.total_volume())
    return render(request, 'workouts/workout_details.html', {"workout": workout})

# CRUD : Adding new x


def add_workout(request, workout_type_id):
    '''
        Creates a Workout of workout_type for the current day
    '''
    day = get_or_create_day(request.user, request.POST['selected_date'])
    workout_type = WorkoutType.objects.get(pk=workout_type_id)
    workout = Workout(day=day,
                      workout_type=workout_type,
                      is_active=True)
    workout.save()
    return render(request,
                  'workouts/active_workout.html',
                  context={"workout": workout})


def add_lift_from_template(request, lift_id):
    ''' Populate new lift with old benchmarks '''
    lift = get_object_or_404(Lift, pk=lift_id)
    previous_sets = lift.sets.all()
    # -- create new lift
    lift_duplicate = copy(lift)
    lift_duplicate.pk = None             # don't overwite previous lift
    lift_duplicate.is_template = False   # don't create another template
    lift_duplicate.workout = Workout.objects.get(
        day__user=request.user, is_active=True)
    lift_duplicate.save()
    # -- duplicate previous sets
    forms = []
    for s in previous_sets:
        form = SetForm(instance=s)
        forms.append(form)
    return render(request,
                  'workouts/active_lift.html',
                  {"lift": lift_duplicate,
                   "templated": True,
                   "sets": forms})


def add_lift_template(request, lift_id):
    ''' button on lift list to turn into template '''
    lift = Lift.objects.get(pk=lift_id)
    lift.is_template = True
    lift.save()
    return render(request, 'calcounter/checkmark.html')


def add_lift(request):
    '''
        GET : returns entry form
        POST: adds a lift to the current workout
    '''
    if request.POST:
        f = LiftForm(request.POST)
        if f.is_valid():
            url_name = request.resolver_match.url_name
            new_lift = f.save(commit=False)
            bodypart = request.POST.get("bodypart")
            machine = request.POST.get("machine")
            print(f"creating lift with {bodypart} , {machine}")
            bp_code = BODYPARTS_MAP.get(bodypart)
            lift_code = LIFT_TYPES_MAP.get(machine)
            new_lift.lift_type = lift_code
            new_lift.bodypart = bp_code
            if url_name == 'addl':
                cur_workout = Workout.objects.get(
                    day__user=request.user, is_active=True)
                new_lift.workout = cur_workout
                new_lift.save()
                context = {
                    "lift": new_lift,
                    "templated": False,
                    "set_form": SetForm()
                }
                return render(request, 'workouts/active_lift.html', context)
            else:  # submit form from dashboard
                new_lift.is_template = True
                new_lift.user = request.user
                new_lift.save()
                return lift_overview_dashboard(request)
    bodypart = request.GET.get("bodypart")
    machine = request.GET.get("machine")
    form = LiftForm()
    url_name = request.resolver_match.url_name
    context = {"form": form, "bodypart": bodypart, "machine": machine}
    if url_name == 'addl':
        context['in_overview'] = False
    elif url_name == 'get_lift_form':
        context['in_overview'] = True
    return render(request, 'workouts/lift_entry.html', context)


def edit_active_workout_lift(request, lift_id):
    ''' returns the active lift with templated=False '''
    lift = get_object_or_404(Lift, pk=lift_id)
    context = {
        "lift": lift,
        "templated": False,
        "set_form": SetForm()
    }
    return render(request, 'workouts/active_lift.html', context)


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
            return render(request,
                          "workouts/set_row.html",
                          {"set": set_obj})
    form = SetForm()
    return render(request,
                  "workouts/set_entry.html",
                  {"form": form, "lift": lift, "editing": False})


def edit_set(request, set_id):
    '''
        GET: prefilled set entry
        POST: save existing set
        with editing=True
    '''
    set_obj = get_object_or_404(Set, pk=set_id)
    if request.method == "POST":
        form = SetForm(request.POST, instance=set_obj)
        if form.is_valid():
            upt_set = form.save()
            return render(request,
                          "workouts/set_row.html",
                          {"set": upt_set})
    form = SetForm(instance=set_obj)
    return render(request, 'workouts/set_entry.html',
                  {"form": form, "set": set_obj, "editing": True})

# CRUD : Deleting / Ending active x


def end_lift(request, lift_id):
    '''
        OOB swap: appends lift to lift_list
        returns active_workout_info (dashboard) 
    '''
    lift = get_object_or_404(
        Lift, pk=lift_id, workout__day__user=request.user)
    workout = lift.workout
    lifts = workout.lifts.all()
    total = workout.total_volume()
    lift_list = render_to_string('workouts/lifts.html',
                                 {"lifts": lifts,
                                  "active": True, }, request=request)
    return render(request,
                  'workouts/end_lift.html',
                  {"workout": workout,
                   "total": total,
                   "lift_list_html": lift_list})


def delete_set(request, set_id):
    set_obj = Set.objects.get(pk=set_id)
    set_obj.delete()
    return HttpResponse()


def end_workout(request):
    cur_workout = Workout.objects.get(is_active=True, day__user=request.user)
    cur_workout.is_active = False
    cur_workout.save()
#    workouts = Workout.objects.get(day__user=request.user)
    return render(request, 'workouts/workout_history.html')


def del_workout(request, workout_id):
    ''' deletes the workout '''
    workout = Workout.objects.get(pk=workout_id)
    workout.delete()
    return HttpResponse()


def back(request):
    ''' cancels the workout '''
    return render(request, 'workouts/start_workout.html')


def clear(request):
    '''returns empty'''
    return HttpResponse("")



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


# lift details

def weekly_sets_dashboard(request):
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
    
    return render(request, 'workouts/weekly_sets.html', ctx)

def lift_overview_dashboard(request):
    ''' Return list of all templated lifts '''
    lifts = Lift.objects.filter(
        Q(user=request.user, is_template=True) | 
        Q(workout__day__user=request.user, is_template=True)
    )
    ctx = {
        "lifts": lifts
    }
    return render(request, 'workouts/lift_overview.html', ctx)