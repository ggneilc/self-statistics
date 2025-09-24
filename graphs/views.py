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
        iso_year, iso_week, iso_weekday = d.date.isocalendar()  # weekday: 1 (Mon)–7 (Sun)
        structured.append({
            "id": d.id,
            "year": iso_year,
            "week": iso_week,
            "day": iso_weekday - 1,  # convert to 0-indexed: 0 (Mon)–6 (Sun)
            "date": d.date.isoformat(),
            "ratio": round(d.calorie_ratio, 2)
        })

    return render(request, "graphs/calendar.html", {"day_data": json.dumps(structured)})
  
def tile_map(request):
    days = Day.objects.filter(user=request.user)
    tmp = []
    for d in days:
        tmp.append({
            "day": d.date.isoformat(),
            "score": d.calorie_ratio 
        })
    return render(request, 'graphs/tile.html', {"day_data": json.dumps(tmp)})

def get_bw_graph(request):
    '''
        displays graph of previous weights
    '''
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
    days = Day.objects.filter(user=request.user).order_by('-date')
    if days.exists():
        if len(days) > 5:
            days = (days)[:4]
        graph_html = plot_calories_per_day(days)
        return render(request, 'graphs/calorie_graph.html', {'graph_html': graph_html})
    else:
        return HttpResponse("graph")


def plot_calories_per_day(days):
    """
    Given a list of day objects with .date and .total_calories,
    return a Plotly bar chart HTML.
    """
    # Extract data for the x and y axes
    x = [str(day.date) for day in days]
    y = [day.calories_consumed for day in days]

    # Create a bar chart
    fig = go.Figure(
        data=[
            go.Bar(
                x=x,
                y=y,
                marker_color='lightsalmon',
                name='Calories'
            )
        ]
    )

    # Customize layout
    fig.update_layout(
        title='Calories Consumed Per Day',
        xaxis_title='Date',
        yaxis_title='Calories',
        paper_bgcolor='#273043',
        plot_bgcolor='#273043',
        font_color="#000",
        width=400,
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    # Return as HTML to embed in a Django template
    return plot(fig, output_type='div', include_plotlyjs=False, config={'responsive': True})

