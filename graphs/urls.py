from django.urls import path

from . import views

app_name = "graphs"
urlpatterns = [
    path("graph/analytics/", views.get_bw_cal_time, name="main-graph"),
    path("graph/analytics/bw-sum/", views.get_bw_summary, name="bw-summary"),
    path("graph/analytics/nutrition-sum/", views.get_nutrition_summary, name="nutrition-summary"),
    path("calendar/", views.calendar_heatmap, name="calendar"),
    path("graph/lift/<str:lift_name>/orm", views.get_lift_graph_orm, name="lift_orm"),
    path("nutrient/macros", views.get_macro_breakdown, name="macros"),
    path("nutrient/minerals", views.get_mineral_breakdown, name="minerals"),
    path("nutrient/vitamins", views.get_vitamin_breakdown, name="vitamins"),
    path("nutrient/overview", views.get_nutrient_overview, name="nutrient-overview"),
]
