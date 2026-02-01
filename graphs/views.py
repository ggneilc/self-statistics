"""
    Graphs interact solely with Day objects and display them
    - Calendar  : shows high level overview and averages of metrics
    - Graphs    : displays simple d3 line graphs of x over time
"""
from datetime import timedelta
import pandas as pd
import numpy as np
from django.shortcuts import render
from django.template.loader import render_to_string
from core.models import Day, RDA_LOOKUP
from calcounter.models import Food
from workouts.models import Lift, Workout
import json
from datetime import date, datetime
from calendar import monthrange



# === Graph Display Container === #

def calendar_container(request):
    return render(request, 'graphs/calendar_area.html')


def trend_container(request):
    return render(request, 'graphs/trend_area.html')

# === Calendars ===

def get_days_of_month(user, selected_date=None):
    if selected_date:
        today = datetime.strptime(selected_date, "%Y-%m-%d").date()
    else:
        today = date.today()
    start = today.replace(day=1)
    end = today.replace(day=monthrange(today.year, today.month)[1])
    return user.days.filter(date__range=(start, end))

# 1 month
def calendar_heatmap(request):
    ''' displays AMDAP calendar : 25x21 grid of rects '''
#    data = get_days_of_month(request.user)
    data = request.user.days.all().exclude(date=date(1, 1, 1))
    print(f"{data=}")
    days = [
        {"id": d.id, "date": d.date.isoformat(), "ratio": round(d.calorie_ratio, 2)}
        for d in data
    ]
    return render(request, "graphs/calendar.html", {"day_data": json.dumps(days)})


def weekly_calendar(request):
    ''' display 7x1 grid of rects '''
    days = Day.objects.filter(user=request.user)
    days = [d for d in days if d.date.isoformat() != "0001-01-01"]
    days = days[:7]
    avg_cals = sum([d.calories_consumed for d in days])/7
    avg_bw = sum(
        [d.bodyweight if d.bodyweight is not None else 0 for d in days])/7
    structured = []
    for d in days:
        # weekday: 1 (Mon)–7 (Sun)
        iso_year, iso_week, iso_weekday = d.date.isocalendar()
        structured.append({
            "id": d.id,
            "year": iso_year,
            "week": iso_week,
            "day": iso_weekday - 1,  # convert to 0-indexed: 0 (Mon)–6 (Sun)
            "date": d.date.isoformat(),
            "ratio": round(d.calorie_ratio, 2)
        })
    return render(request, "graphs/weekly_calendar.html",
                  {"day_data": json.dumps(structured),
                   "avg_cals": avg_cals,
                   "avg_bw": avg_bw})


# === Line Graphs ===
    
def get_lift_history(user, exercise_name):
    return Lift.objects.filter(
        workout__day__user=user,
        exercise_name__iexact=exercise_name # Use iexact to be case-insensitive
    ).select_related(
        'workout__day' # Join these tables to avoid N+1 queries in the template
    ).prefetch_related(
        'sets' # Load the reps/weight data in one go
    ).order_by(
        'workout__day__date'
    )


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


def get_bw_graph(request):
    '''Time series of Bodyweight / Day'''
    df, _, stats = get_bodyweight_summary(request)
    df = df.dropna(subset=['bodyweight'])
    data = [
        {
            "day": row.Index.isoformat(),
            "value": row.bodyweight,
            "ma7": row.weight_ma7
        }
        for row in df.itertuples()
    ]
    summary = render_to_string('graphs/bodyweight_summary.html',
                               context=stats, request=request)
    context = {
        "day_data": json.dumps(data),
        "summary": summary
    }
    return render(request, 'graphs/bw-time.html', context)


def get_bw_weekly(request):
    ''' return weekly bodyweight graph '''
    _, timed_interval, stats = get_bodyweight_summary(request, time=7)
    weekly_weights = timed_interval.dropna().round(2).astype(float)
    data = [
        {"day": date.isoformat(), "value": bodyweight}
        for date, bodyweight in weekly_weights.items()
    ]
    summary = render_to_string('graphs/bodyweight_summary.html',
                               context=stats, request=request)
    context = {
        "day_data": json.dumps(data),
        "summary": summary
    }
    return render(request, 'graphs/bw-time.html', context)


def get_bw_monthly(request):
    ''' return weekly bodyweight graph '''
    _, timed_interval, stats = get_bodyweight_summary(request, time=30)
    monthly_weights = timed_interval.dropna().round(2).astype(float)
    data = [
        {"day": date.isoformat(), "value": bodyweight}
        for date, bodyweight in monthly_weights.items()
    ]
    summary = render_to_string('graphs/bodyweight_summary.html',
                               context=stats, request=request)
    context = {
        "day_data": json.dumps(data),
        "summary": summary
    }
    return render(request, 'graphs/bw-time.html', context)


def get_cal_graph(request):
    '''Time series of Calories / Day'''
#    df, _, stats = get_calorie_summary(request)
#    df = df.dropna(subset=['cals'])
#    summary = render_to_string('graphs/calorie_summary.html',
#                               context=stats, request=request)
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
    context = {
        "day_data": json.dumps(data),
    }
    return render(request, 'graphs/cal-time.html', context)


def get_cals_weekly(request):
    ''' return weekly calorie graph '''
    _, timed_interval, stats = get_calorie_summary(request, time=7)
    weekly_weights = timed_interval.dropna().round(2).astype(float)
    data = [
        {"day": date.isoformat(), "value": bodyweight}
        for date, bodyweight in weekly_weights.items()
    ]
    summary = render_to_string('graphs/calorie_summary.html',
                               context=stats, request=request)
    context = {
        "day_data": json.dumps(data),
        "summary": summary
    }
    return render(request, 'graphs/cal-time.html', context)


def get_cals_monthly(request):
    ''' return weekly calorie graph '''
    _, timed_interval, stats = get_calorie_summary(request, time=30)
    monthly_weights = timed_interval.dropna().round(2).astype(float)
    data = [
        {"day": date.isoformat(), "value": bodyweight}
        for date, bodyweight in monthly_weights.items()
    ]
    summary = render_to_string('graphs/calorie_summary.html',
                               context=stats, request=request)
    context = {
        "day_data": json.dumps(data),
        "summary": summary
    }
    return render(request, 'graphs/cal-time.html', context)


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


def get_type_stats(request, type_id):
    workouts = (
        Workout.objects.filter(day__user=request.user, workout_type=type_id)
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

    data = [
        {
            "day": row.Index.isoformat(),
            "value": row.total_volume,
        }
        for row in df.itertuples()
    ]
    workout_types = request.user.workout_types.all()
    stats = get_workout_type_summary(df)
    summary = render_to_string('graphs/volume_summary.html',
                               context=stats, request=request)
    context = {
        "day_data": json.dumps(data),
        "summary": summary,
        "workout_types": workout_types
    }
    return render(request, 'graphs/volume-time.html', context)


# === Macro breakdown Pie Charts ===


def get_macro_breakdown(request):
    ''' return macro breakdown for a specific date '''
    day = Day.objects.get(user=request.user, date=request.GET.get("selected_date"))
    carbs, protein, fat = day.macro_breakdown
    total = day.calories_consumed
    goals = {}
    data = {
        'Sleep': day.sleep,
        'Water': day.water_consumed,
        'Fat': fat,
        'Carbs': carbs,
        'Protein': protein,
        'Calories': total,
    }
    goals = {
        'Sleep': day.sleep_goal,
        'Water': day.water_goal,
        'Fat': round((day.calorie_goal - (day.protein_goal * 4)) * 0.3 / 9),
        'Carbs': round((day.calorie_goal - (day.protein_goal * 4)) * 0.7 / 4),
        'Protein': day.protein_goal,
        'Calories': day.calorie_goal,
    }
    context = {
        "day_data": json.dumps(data),
        "goals": json.dumps(goals)
    }
    return render(request, 'graphs/macro-pie.html', context)

def get_mineral_breakdown(request):
    gender = request.user.profile.gender  # 'M' or 'F'
    age = request.user.profile.age  # integer
    day = Day.objects.get(user=request.user, date=request.GET.get("selected_date"))
    if age < 19:
        goal_type = 'Young ' + 'Male' if gender == 'M' else 'Female'
    else:
        goal_type = 'Adult ' +  'Male' if gender == 'M' else 'Female'
    goals = {}
    for mineral, values in RDA_LOOKUP['Minerals'].items():
        goals[mineral] = values[goal_type]
    
    data = day.mineral_breakdown
    context = {
        "day_data": json.dumps(data),
        "goals": json.dumps(goals)
    }
    return render(request, 'graphs/mineral-pie.html', context)

def get_vitamin_breakdown(request):
    gender = request.user.profile.gender  # 'M' or 'F'
    age = request.user.profile.age  # integer
    day = Day.objects.get(user=request.user, date=request.GET.get("selected_date"))
    if age < 19:
        goal_type = 'Young ' + 'Male' if gender == 'M' else 'Female'
    else:
        goal_type = 'Adult ' +  'Male' if gender == 'M' else 'Female'
    goals = {}
    for vitamin, values in RDA_LOOKUP['Vitamins'].items():
        goals[vitamin] = values[goal_type]
    
    data = day.vitamin_breakdown
    context = {
        "day_data": json.dumps(data),
        "goals": json.dumps(goals)
    }
    return render(request, 'graphs/vitamin-pie.html', context)

# === Statistics Computations ===


def get_bodyweight_summary(request, time=7):
    ''' fill summary statistics under bodyweight '''
    # -- create dataframe
    data = request.user.days.all().exclude(date=date(1, 1, 1))
    df = pd.DataFrame([
        {"date": d.date, "bodyweight": d.bodyweight}
        for d in data
    ])
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    # -- timed intervals
    if (time == 7):
        weekly_weights = df["bodyweight"].resample("W").mean()
    elif (time == 30):
        weekly_weights = df["bodyweight"].resample("M").mean()
    # -- moving average
    df["weight_ma7"] = df["bodyweight"].rolling(7, min_periods=1).mean()
    # -- average weight (mean)
#    data = [d.bodyweight for d in data if d.bodyweight is not None]
    avg_weight = df['bodyweight'].mean()
    # -- daily weight fluctation (stddev of diff)
    df['diff'] = df['bodyweight'].diff()
    fluctation = df['diff'].std()
    # -- 7d difference
    df['weight_7d_ago'] = df['bodyweight'].shift(freq='7D')
    bw_7d_diff = df['bodyweight'].iloc[0] - df['weight_7d_ago'].iloc[0]
    # -- biggest drop
    max_drawdown = df['diff'].min()
    max_runup = df['diff'].max()
    # -- simple stats
    total_change = df['bodyweight'].iloc[0] - df['bodyweight'].min()
    # -- linear regression slope (trend)
    df_cleaned = df['bodyweight'].dropna()
    x = np.arange(len(df_cleaned))
    y = df_cleaned.values
    slope, intercept = np.polyfit(x, y, 1)
    stats = {
        "mean": round(float(avg_weight), 2),
        "stddev": round(float(fluctation), 2),
        "trend": round(float(slope), 2),
        "intercept": round(float(intercept), 2),
        "7d": round(float(bw_7d_diff), 2),
        "max_drawdown": round(float(max_drawdown), 2),
        "max_runup": round(float(max_runup), 2),
        "max": df['bodyweight'].max(),
        "min": df['bodyweight'].min(),
        "total_change": round(float(total_change), 2)
    }
    return df, weekly_weights, stats


def get_calorie_summary(request, time=7):
    # -- create dataframe
    data = request.user.days.all().exclude(date=date(1, 1, 1))
    df = pd.DataFrame([
        {"date": d.date,
         "cals": d.calories_consumed,
         "pro": d.protein_consumed}
        for d in data
        if d.calories_consumed != 0
    ])
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    # -- timed intervals
    if (time == 7):
        weekly_weights = df["cals"].resample("W").mean()
    elif (time == 30):
        weekly_weights = df["cals"].resample("M").mean()
    # -- moving average
    df["weight_ma7"] = df["cals"].rolling(7, min_periods=1).mean()
    # -- average weight (mean)
    avg_cals = df['cals'].mean()
    avg_pro = df['pro'].mean()
    # -- daily weight fluctation (stddev of diff)
    df['diff_c'] = df['cals'].diff()
    fluctation_c = df['diff_c'].std()
    df['diff_p'] = df['pro'].diff()
    fluctation_p = df['diff_p'].std()
    # -- most eaten meal

    from django.db.models import Count

    top_meal = (
        Food.objects.filter(day__user=request.user)
        .values("name")
        .annotate(count=Count("id"))
        .order_by("-count")
        .first()
    )
    # -- biggest drop
    max_drawdown = df['diff_c'].min()
    max_runup = df['diff_c'].max()
    # -- simple stats
    total_change = df['cals'].iloc[0] - df['cals'].min()
    stats = {
        "mean_c": round(float(avg_cals), 2),
        "mean_p": round(float(avg_pro), 2),
        "stddev_c": round(float(fluctation_c), 2),
        "stddev_p": round(float(fluctation_p), 2),
        "meal": top_meal['name'],
        "count": top_meal['count'],
        "max_drawdown": round(float(max_drawdown), 2),
        "max_runup": round(float(max_runup), 2),
        "max": df['cals'].max(),
        "min": df['cals'].min(),
        "total_change": round(float(total_change), 2)
    }
    return df, weekly_weights, stats


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
