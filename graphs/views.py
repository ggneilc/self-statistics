from django.shortcuts import render, HttpResponse
from core.models import Day
from calcounter.models import Food
from workouts.models import Workout, Lift
import json

import pandas as pd
from datetime import datetime, date


def calendar_heatmap(request):
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


def yearly_calendar(request):
    ''' display 27x14 grid of rects '''
    days = Day.objects.filter(user=request.user)
    days = [d for d in days if d.date.isoformat() != "0001-01-01"]


def get_bw_graph(request):
    '''Time series of Bodyweight / Day'''
    days = Day.objects.filter(user=request.user).exclude(date=date(1, 1, 1))
    tmp = []
    for d in days:
        if d.bodyweight is not None and d.bodyweight > 100 and d.bodyweight < 200:
            tmp.append({
                "day": d.date.isoformat(),
                "value": d.bodyweight
            })
        else:
            pass
    return render(request, 'graphs/bw-time.html', {"day_data": json.dumps(tmp)})


def get_cal_graph(request):
    '''Time series of Calories / Day'''
