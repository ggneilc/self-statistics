from django.shortcuts import render, HttpResponse
from .models import Workout, WorkoutType
from .forms import LiftForm, WTypeForm
from datetime import datetime
from random import randint

# Create your views here.

def add_workout(request):
    '''
        opens a workout for the day to add lifts to 
    '''
    workout = Workout(user=request.user, 
                      date=datetime.today(),
                      is_active=True)
    workout.save()
    return load_workout_entry(request)

def get_lifts(request, workout_id):
    workout = Workout.objects.get(pk=workout_id)
    lifts = workout.lifts.all()
    total = sum((lift.sets * lift.reps * lift.weight) for lift in lifts)
    return render(request, 'workouts/lift.html', context={"lifts": lifts, "total":int(total), "id": workout_id})

def add_lift(request):
    '''
        POST:
            adds a lift to the current workout
        GET:
            returns entry form
    '''
    if request.POST:
        f = LiftForm(request.POST)
        if f.is_valid():
            try:
                cur_workout = Workout.objects.filter(is_active=True, user=request.user)[0]
            except IndexError:
                return HttpResponse("""
                <p hx-get=\"/workouts/list\"
                    hx-trigger=\"load delay:1s\"
                    hx-target=\"#workout_list__container\">
                    No active workout!
                </p>
                                    """)

            new_lift = f.save(commit=False)
            new_lift.workout = cur_workout
            new_lift.save()
            return HttpResponse("""
                <p>success<p hx-get=\"/workouts/list\"
                                hx-target=\"#workout_list__container\"
                                hx-trigger=\"load delay:500ms\">
                                """)
        else:
            form = LiftForm()
    else:
        form = LiftForm()
    return render(request, 'workouts/lift_entry.html', {"form": form})

def end_workout(request):
    '''
        closes current workout
    '''
    cur_workout = Workout.objects.get(is_active=True, user=request.user)
    cur_workout.is_active = False
    cur_workout.save()
    return render(request, 'workouts/workout_refresh.html')

def get_workouts(request):
    '''
        returns a list of users workouts
    '''
    if has_active_workout(request.user):
        return show_active_workout(request)
    workouts = Workout.objects.filter(user=request.user).order_by('-date')
    return render(request, 'workouts/workout_list.html', context={"workouts": workouts})

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

def set_workout_type(request, workout_id):
    '''
        sets the active workout's type and displays add_lift
    '''
    workout = Workout.objects.get(user=request.user, is_active=True)
    workout_type = WorkoutType.objects.get(pk=workout_id)
    workout.workout_type = workout_type
    workout.save()
    return render(request, 'workouts/active_workout.html', context={"workout": workout})

def show_active_workout(request):
    workout = Workout.objects.get(user=request.user, is_active=True)
    return render(request, 'workouts/active_workout.html', context={"workout": workout})

def del_workout(request, workout_id):
    '''
        deletes the workout
    '''
    workout = Workout.objects.get(pk=workout_id)
    workout.delete()
    return HttpResponse()

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
        is_active = Workout.objects.filter(user=user, is_active=True)[0]
        return is_active  #, True  # bool flag
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
    