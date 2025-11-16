"""
    Graphs interact solely with Day objects and display them
    - Calendar  : shows high level overview and averages of metrics
    - Graphs    : displays simple d3 line graphs of x over time
"""
import pandas as pd
import numpy as np
from django.shortcuts import render
from django.template.loader import render_to_string
from core.models import Day
from workouts.models import Workout
import json
from datetime import date


# === Graph Display Container === #

def calendar_container(request):
    return render(request, 'graphs/calendar_area.html')


def trend_container(request):
    return render(request, 'graphs/trend_area.html')

# === Calendars ===


def calendar_heatmap(request):
    ''' displays AMDAP calendar : 25x21 grid of rects '''
    days = Day.objects.filter(user=request.user)
    days = [d for d in days if d.date.isoformat() != "0001-01-01"]
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
    return render(request, "graphs/calendar.html",
                  {"day_data": json.dumps(structured)})


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


def get_bw_graph(request):
    '''Time series of Bodyweight / Day'''
    df, _, stats = get_bodyweight_summary(request)
    df = df.dropna(subset=['bodyweight'])
    print(f"{df=}")
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
    days = Day.objects.filter(user=request.user).exclude(date=date(1, 1, 1))
    tmp = []
    for d in days:
        if d.calories_consumed == 0:
            continue
        day_str = d.date.isoformat()
        tmp.append({
            "day": day_str,
            "value": d.calories_consumed,
        })
    return render(request, 'graphs/cal-time.html', {"day_data": json.dumps(tmp)})


def get_volume_graph(request):
    '''Time series of Volume / Day'''
    days = Day.objects.filter(user=request.user).exclude(date=date(1, 1, 1))
    tmp = []
    for d in days:
        total = sum(w.total_volume() for w in d.workouts.all())
        if total == 0:
            continue
        tmp.append({
            "day": d.date.isoformat(),
            "value": total
        })
    return render(request, 'graphs/cal-time.html', {"day_data": json.dumps(tmp)})

# === Statistics Computations ===


def get_bodyweight_summary(request, time=7):
    ''' fill summary statistics under bodyweight '''
    data = request.user.days.all().exclude(date=date(1, 1, 1))
    df = pd.DataFrame([
        {"date": d.date, "bodyweight": d.bodyweight}
        for d in data
    ])
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    if (time == 7):
        weekly_weights = df["bodyweight"].resample("W").mean()
    elif (time == 30):
        weekly_weights = df["bodyweight"].resample("M").mean()

    print(f"{weekly_weights=}")
    df["weight_ma7"] = df["bodyweight"].rolling(7, min_periods=1).mean()
    print(f"{df["weight_ma7"]=}")
    # average weight (mean)
    # sum(x) / len(x)
    data = [d.bodyweight for d in data if d.bodyweight is not None]
    avg_weight = (sum(data) / len(data))
    print(f"{avg_weight=}")
    # weight fluctation (stddev)
    df['diff'] = df['bodyweight'].diff()
    fluctation = df['diff'].std()
    print(f"{fluctation=}")
    # 7d difference
    df['weight_7d_ago'] = df['bodyweight'].shift(freq='7D')
    print(f"{df.iloc[0]=}")
    bw_7d_diff = df['bodyweight'].iloc[0] - df['weight_7d_ago'].iloc[0]

    # biggest drop
    max_drawdown = df['diff'].min()
    max_runup = df['diff'].max()

    # simple stats

    total_change = df['bodyweight'].iloc[0] - df['bodyweight'].min()

    # linear regression slope (trend)
    df_cleaned = df['bodyweight'].dropna()
    x = np.arange(len(df_cleaned))
    y = df_cleaned.values
    slope, intercept = np.polyfit(x, y, 1)
    print(f"{slope=}, {intercept=}")
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
