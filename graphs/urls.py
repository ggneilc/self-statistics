from django.urls import path

from . import views

app_name = "graphs"
urlpatterns = [
    path("calendar/", views.calendar_heatmap, name="calendar"),
    path("graph/bodyweight", views.get_bw_graph, name="bw"),
    path("graph/calories", views.get_cal_graph, name="cals"),
]
