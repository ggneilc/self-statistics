from django.urls import path

from . import views

app_name = "graphs"
urlpatterns = [
    path("calendar/view", views.calendar_container, name="calendar_area"),
    path("trend/view", views.trend_container, name="trend_area"),
    path("nutrient/macros", views.get_macro_breakdown, name="macros"),
    path("nutrient/minerals", views.get_mineral_breakdown, name="minerals"),
    path("nutrient/vitamins", views.get_vitamin_breakdown, name="vitamins"),
    path("calendar/", views.calendar_heatmap, name="calendar"),
    path("calendar/weekly", views.weekly_calendar, name="week"),
    path("graph/bodyweight", views.get_bw_graph, name="bw"),
    path("graph/bodyweight/weekly", views.get_bw_weekly, name="bw-weekly"),
    path("graph/bodyweight/monthly", views.get_bw_monthly, name="bw-monthly"),
    path("graph/calories", views.get_cal_graph, name="cals"),
    path("graph/calories/weekly", views.get_cals_weekly, name="cals-weekly"),
    path("graph/calories/monthly", views.get_cals_monthly, name="cals-monthly"),
    path("graph/volume", views.get_volume_graph, name="vol"),
    path("graph/volume/<int:type_id>", views.get_type_stats, name="w_type_graph"),
    path("graph/lift/<str:lift_name>/orm", views.get_lift_graph_orm, name="lift_orm"),

]
