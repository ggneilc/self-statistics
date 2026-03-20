"""
    Graphs interact solely with Day objects and display them
    - Calendar  : shows high level overview and averages of metrics
    - Graphs    : displays simple d3 line graphs of x over time
"""
from datetime import timedelta
import pandas as pd
import numpy as np
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from core.models import Day, RDA_LOOKUP, get_goal_type
from calcounter.models import Food
from workouts.models import Lift, Workout
import json
from datetime import date, datetime
from calendar import monthrange



# === Calendars ===

@login_required
def calendar_heatmap(request):
    """Display calendar heatmap. Template (1-week vs 2-week window)
    is chosen based on the user's profile setting.
    """
    data = request.user.days.all().exclude(date=date(1, 1, 1))
    days = [
        {"id": d.id, "date": d.date.isoformat(), "ratio": round(d.calorie_ratio, 2)}
        for d in data
    ]
    template_name = "graphs/calendar.html"
    profile = getattr(request.user, "profile", None)
    if profile and getattr(profile, "calendar_view", "2w") == "1w":
        template_name = "graphs/one-week-calendar.html"
    return render(request, template_name, {"day_data": json.dumps(days)})



# === Line Graphs ===
    
def get_lift_history(user, exercise_name):
    return Lift.objects.filter(
        workout__day__user=user,
        movement__name__iexact=exercise_name # Use iexact to be case-insensitive
    ).select_related(
        'workout__day' # Join these tables to avoid N+1 queries in the template
    ).prefetch_related(
        'sets' # Load the reps/weight data in one go
    ).order_by(
        'workout__day__date'
    )


@login_required
def get_lift_graph_orm(request, lift_name):
    history = get_lift_history(request.user, lift_name)
    data = []
    for lift in history:
        orm = lift.estimated_1rm()
        if orm:
            data.append({
                "date": lift.workout.day.date.isoformat(),
                "one_rm": round(orm, 2),
            })
    return render(request, "graphs/lift_graph_orm.html", {'data': json.dumps(data)})


@login_required
def get_bw_cal_time(request):
    '''
    Time series of Bodyweight / Cals / Day 
        : bodyweight is line chart with 7 day moving average
        : calories is bar chart
    '''
    data = request.user.days.all().exclude(date=date(1, 1, 1)).order_by('date')
    df = pd.DataFrame([
        {
            "date": d.date, 
            "bodyweight": d.bodyweight,
            "calories": d.calories_consumed
        }
        for d in data
    ])
    
    out_data = []
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        
        # moving average for bodyweight
        df["weight_ma7"] = df["bodyweight"].rolling(7, min_periods=1).mean()
        
        # replace NaN with None for json serialization
        df_clean = df.replace({np.nan: None})
        
        for row in df_clean.itertuples():
            out_data.append({
                "day": row.Index.isoformat(),
                "bodyweight": row.bodyweight,
                "ma7": row.weight_ma7,
                "calories": row.calories
            })
            
    context = {"day_data": json.dumps(out_data)}
    return render(request, 'graphs/bw-cal-time.html', context)

# Unused
@login_required
def get_bw_graph(request):
    '''Time series of Bodyweight / Day'''
    df, _, _ = get_bodyweight_summary(request)
    df = df.dropna(subset=['bodyweight'])
    data = [
        {
            "day": row.Index.isoformat(),
            "value": row.bodyweight,
            "ma7": row.weight_ma7
        }
        for row in df.itertuples()
    ]
    context = {"day_data": json.dumps(data)}
    return render(request, 'graphs/bw-time.html', context)

@login_required
def get_cal_graph(request):
    '''Time series of Calories / Day'''
    days = request.user.days.all().exclude(date=date(1, 1, 1))
    data = [
        {
         "date": d.date.isoformat(),
         "calories": d.calories_consumed,
         "carbs": (w := d.macro_breakdown)[0],
         "protein": w[1],
         "fat": w[2]
        }
        for d in days
    ]
    context = {"day_data": json.dumps(data)}
    return render(request, 'graphs/cal-time.html', context)

# Unused
@login_required
def get_volume_graph(request):
    '''Time series of Volume / Day'''
    days = Day.objects.filter(user=request.user).exclude(date=date(1, 1, 1))
    stats = get_volume_summary(request)
    summary = render_to_string('graphs/volume_summary.html',
                               context=stats, request=request)
    tmp = []
    for d in days:
        total = sum(w.total_volume() for w in d.workouts.all())
        if total == 0:
            continue
        tmp.append({
            "day": d.date.isoformat(),
            "value": total
        })
    workout_types = request.user.workout_types.all()
    context = {
        "day_data": json.dumps(tmp),
        "summary": summary,
        "workout_types": workout_types
    }
    return render(request, 'graphs/volume-time.html', context)



# === Macro breakdown Pie Charts ===

@login_required
def get_macro_breakdown(request):
    ''' return macro breakdown for a specific date '''
    day = get_object_or_404(Day, user=request.user, date=request.GET.get("selected_date"))
    carbs, protein, fat = day.macro_breakdown
    total = day.calories_consumed
    goals = {}
    data = {
        'Calories': total,
        'Protein': protein,
        'Carbs': carbs,
        'Fat': fat,
        'Water': day.water_consumed,
        'Sleep': day.sleep,
    }
    goals = {
        'Calories': day.calorie_goal,
        'Protein': day.protein_goal,
        'Carbs': round((day.calorie_goal - (day.protein_goal * 4)) * 0.7 / 4),
        'Fat': round((day.calorie_goal - (day.protein_goal * 4)) * 0.3 / 9),
        'Water': day.water_goal,
        'Sleep': day.sleep_goal,
    }
    context = {
        "day_data": json.dumps(data),
        "goals": json.dumps(goals)
    }
    return render(request, 'graphs/macro-pie.html', context)

@login_required
def get_mineral_breakdown(request):
    day = get_object_or_404(Day, user=request.user, date=request.GET.get("selected_date"))
    goal_type = get_goal_type(request.user)
    goals = {}
    for mineral, values in RDA_LOOKUP['Minerals'].items():
        goals[mineral] = values[goal_type]
    data = day.mineral_breakdown
    context = {
        "day_data": json.dumps(data),
        "goals": json.dumps(goals)
    }
    return render(request, 'graphs/mineral-pie.html', context)

@login_required
def get_vitamin_breakdown(request):
    day = get_object_or_404(Day, user=request.user, date=request.GET.get("selected_date"))
    goal_type = get_goal_type(request.user)
    goals = {}
    for vitamin, values in RDA_LOOKUP['Vitamins'].items():
        goals[vitamin] = values[goal_type]
    data = day.vitamin_breakdown
    context = {
        "day_data": json.dumps(data),
        "goals": json.dumps(goals)
    }
    return render(request, 'graphs/vitamin-pie.html', context)

@login_required
def get_nutrient_overview(request):
    day = get_object_or_404(Day, user=request.user, date=request.GET.get("selected_date"))
    carbs, protein, fat = day.macro_breakdown
    total = day.calories_consumed
    goal_type = get_goal_type(request.user)
    
    macro_data = {
        'Calories': total,
        'Protein': protein,
        'Carbs': carbs,
        'Fat': fat,
        'Water': day.water_consumed,
        'Sleep': day.sleep,
    }
    macro_goals = {
        'Calories': day.calorie_goal,
        'Protein': day.protein_goal,
        'Carbs': round((day.calorie_goal - (day.protein_goal * 4)) * 0.7 / 4),
        'Fat': round((day.calorie_goal - (day.protein_goal * 4)) * 0.3 / 9),
        'Water': day.water_goal,
        'Sleep': day.sleep_goal,
    }
    
    mineral_goals = {}
    for mineral, values in RDA_LOOKUP['Minerals'].items():
        mineral_goals[mineral] = values[goal_type]
    mineral_data = day.mineral_breakdown
    
    vitamin_goals = {}
    for vitamin, values in RDA_LOOKUP['Vitamins'].items():
        vitamin_goals[vitamin] = values[goal_type]
    vitamin_data = day.vitamin_breakdown
    
    context = {
        "macro_data": json.dumps(macro_data),
        "macro_goals": json.dumps(macro_goals),
        "mineral_data": json.dumps(mineral_data),
        "mineral_goals": json.dumps(mineral_goals),
        "vitamin_data": json.dumps(vitamin_data),
        "vitamin_goals": json.dumps(vitamin_goals)
    }
    return render(request, 'graphs/all-nutrients.html', context)

# === Statistics Computations ===


def get_bw_summary(request):
    ''' fill summary statistics under bodyweight '''
    # -- create dataframe
    data = request.user.days.all().exclude(date=date(1, 1, 1))
    df = pd.DataFrame([
        {"date": d.date, "bodyweight": d.bodyweight}
        for d in data
    ])
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    # -- average weight (mean)
#    data = [d.bodyweight for d in data if d.bodyweight is not None]
    avg_weight = df['bodyweight'].mean()
    # this weeks 7d average
    this_week = df.index.max() - timedelta(days=df.index.max().weekday())
    this_week_avg = df.loc[:this_week].mean()['bodyweight']
    # -- daily weight fluctation (stddev of diff)
    df['diff'] = df['bodyweight'].diff()
    fluctation = df['diff'].std()
    # -- lbs +/- per week
    weekly_weights = df["bodyweight"].resample("W").mean()
    weekly_diff = weekly_weights.diff()
    pm_per_week = weekly_diff.mean()
    # -- simple stats
    if pd.notna(df['bodyweight'].iloc[0]) and pd.notna(df['bodyweight'].min()):
        total_change = df['bodyweight'].iloc[0] - df['bodyweight'].iloc[-1]
    else:
        total_change = 0
    
    stats = {
        "avg_weight": float(avg_weight),
        "7d_avg": float(this_week_avg),
        "stddev": float(fluctation),
        "total_change": float(total_change),
        "pm_per_week": float(pm_per_week),
    }
    return render(request, 'graphs/bw-summary.html', {'stats': stats})


def get_nutrition_summary(request, time=7):
    # -- create dataframe
    data = request.user.days.all().exclude(date=date(1, 1, 1))
    df = pd.DataFrame([
        {"date": d.date,
         "cals": d.calories_consumed,
         "goal": d.calorie_goal,
         "pro": d.protein_consumed,
         "water": d.water_consumed,
         "carb": d.macro_breakdown[0],
         "fat": d.macro_breakdown[2],
         }
        for d in data
        if d.calories_consumed != 0
    ])
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    # -- simple averages
    avg_cals = df['cals'].mean()
    avg_pro = df['pro'].mean()
    avg_water = df['water'].mean()
    avg_carb = df['carb'].mean()
    avg_fat = df['fat'].mean()
    avg_goal_diff = df['goal'].mean() - df['cals'].mean()
    # -- 7d averages
    weekly_cals = df['cals'].resample("W").mean()
    weekly_pro = df['pro'].resample("W").mean()
    _7d_avg_cals = weekly_cals.dropna().mean()
    _7d_avg_pro = weekly_pro.dropna().mean()
    # -- simple stats
    stats = {
        "mean_c": float(avg_cals),
        "mean_p": float(avg_pro),
        "mean_carb": float(avg_carb),
        "mean_f": float(avg_fat),
        "mean_water": float(avg_water),
        "7d_avg_c": float(_7d_avg_cals),
        "7d_avg_p": float(_7d_avg_pro),
        "stddev_c": float(avg_goal_diff),
    }
    return render(request, 'graphs/nutrition-summary.html', {'stats': stats})


def get_volume_summary(request):
    workouts = (
        Workout.objects.filter(day__user=request.user)
        .exclude(day__date=date(1, 1, 1))
        .select_related("day", "workout_type")
        .prefetch_related("lifts__sets")
        .order_by("-day__date", "-id")
    )
    df = pd.DataFrame([
        {"date": d.day.date, "workout_type": d.workout_type,
            "total_volume": d.total_volume()}
        for d in workouts
    ])
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')

    # --- 1) Workouts per week (last 4 weeks + lifetime avg) ---
    today = df.index.max()
    four_weeks_ago = today - timedelta(weeks=4)

    workouts_last_4_weeks = df.loc[df.index >= four_weeks_ago]
    workouts_per_week_4wk = workouts_last_4_weeks.resample("W").size().mean()
    workouts_per_week_lifetime = df.resample("W").size().mean()
    # --- 3) ACWR (acute–chronic workload ratio) ---
    acute_load = df["total_volume"].last("7D").sum()
    chronic_load = df["total_volume"].last("28D").mean() * 4
    acwr = acute_load / chronic_load if chronic_load > 0 else None

    # -- mean
    avg_volume = df['total_volume'].mean()
    # -- stddev
    weekly_volume = df["total_volume"].resample("W").sum()
    if weekly_volume.mean() > 0:
        weekly_volume_cv = weekly_volume.std() / weekly_volume.mean()
    else:
        weekly_volume_cv = None
    # -- max
    heaviest = df['total_volume'].max()
    # -- streaks
    daily_presence = df["total_volume"].resample("D").size() > 0
    # Current streak: count backward from last workout day
    current_streak = 0
    for v in reversed(daily_presence):
        if v:
            current_streak += 1
        else:
            break
    # Longest streak: scan runs of True values
    longest_streak = 0
    temp = 0
    for v in daily_presence:
        if v:
            temp += 1
            longest_streak = max(longest_streak, temp)
        else:
            temp = 0
    stats = {
        "mean": round(float(avg_volume), 2),
        "stddev": round(float(weekly_volume_cv), 2),
        "max": round(float(heaviest), 2),
        "workout_last_4wk": len(workouts_last_4_weeks),
        "workout_4wk": workouts_per_week_4wk,
        "acute": round(float(acute_load), 2),
        "chronic": round(float(chronic_load), 2),
        "acwr": round(float(acwr), 2),
        "cur_streak": current_streak,
        "long_streak": longest_streak,
    }

    return stats


def get_workout_type_summary(df):
    ''' returns summary for a type of workout, i.e. "push" '''
    # --- 1) Workouts per week (last 4 weeks + lifetime avg) ---
    today = df.index.max()
    four_weeks_ago = today - timedelta(weeks=4)

    workouts_last_4_weeks = df.loc[df.index >= four_weeks_ago]
    workouts_per_week_4wk = workouts_last_4_weeks.resample("W").size().mean()
    workouts_per_week_lifetime = df.resample("W").size().mean()
    # --- 3) ACWR (acute–chronic workload ratio) ---
    acute_load = df["total_volume"].last("7D").sum()
    chronic_load = df["total_volume"].last("28D").mean() * 4
    acwr = acute_load / chronic_load if chronic_load > 0 else None

    # -- mean
    avg_volume = df['total_volume'].mean()
    # -- stddev
    weekly_volume = df["total_volume"].resample("W").sum()
    if weekly_volume.mean() > 0:
        weekly_volume_cv = weekly_volume.std() / weekly_volume.mean()
    else:
        weekly_volume_cv = None
    # -- max
    heaviest = df['total_volume'].max()
    # -- streaks
    daily_presence = df["total_volume"].resample("D").size() > 0
    # Current streak: count backward from last workout day
    current_streak = 0
    for v in reversed(daily_presence):
        if v:
            current_streak += 1
        else:
            break
    # Longest streak: scan runs of True values
    longest_streak = 0
    temp = 0
    for v in daily_presence:
        if v:
            temp += 1
            longest_streak = max(longest_streak, temp)
        else:
            temp = 0
    stats = {
        "mean": round(float(avg_volume), 2),
        "stddev": round(float(weekly_volume_cv), 2),
        "max": round(float(heaviest), 2),
        "workout_last_4wk": len(workouts_last_4_weeks),
        "workout_4wk": round(int(workouts_per_week_4wk)),
        "acute": round(float(acute_load), 2),
        "chronic": round(float(chronic_load), 2),
        "acwr": round(float(acwr), 2),
        "cur_streak": current_streak,
        "long_streak": longest_streak,
    }

    return stats
