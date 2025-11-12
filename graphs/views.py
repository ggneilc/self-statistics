"""
    Graphs interact solely with Day objects and display them
    - Calendar  : shows high level overview and averages of metrics
    - Graphs    : displays simple d3 line graphs of x over time
"""
from django.shortcuts import render
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
    days = Day.objects.filter(user=request.user).exclude(date=date(1, 1, 1))
    tmp = []
    for d in days:
        if d.bodyweight is not None and d.bodyweight > 0:
            tmp.append({
                "day": d.date.isoformat(),
                "value": d.bodyweight
            })
        else:
            pass
    return render(request, 'graphs/bw-time.html', {"day_data": json.dumps(tmp)})


def get_cal_graph(request):
    '''Time series of Calories / Day'''
    days = Day.objects.filter(user=request.user).exclude(date=date(1, 1, 1))
    tmp = []
    for d in days:
        if d.calories_consumed == 0:
            continue
        tmp.append({
            "day": d.date.isoformat(),
            "value": d.calories_consumed
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
