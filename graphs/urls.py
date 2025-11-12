from django.urls import path

from . import views

app_name = "graphs"
urlpatterns = [
    path("calendar/view", views.calendar_container, name="calendar_area"),
    path("trend/view", views.trend_container, name="trend_area"),
    path("calendar/", views.calendar_heatmap, name="calendar"),
    path("calendar/weekly", views.weekly_calendar, name="week"),
    path("graph/bodyweight", views.get_bw_graph, name="bw"),
    path("graph/calories", views.get_cal_graph, name="cals"),
    path("graph/volume", views.get_volume_graph, name="vol"),
]
