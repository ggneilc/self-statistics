from django.urls import path

from . import views

app_name = "graphs"
urlpatterns = [
    path("graph/analytics/", views.get_bw_cal_time, name="main-graph"),
    path("calendar/", views.calendar_heatmap, name="calendar"),
    path("graph/lift/<str:lift_name>/orm", views.get_lift_graph_orm, name="lift_orm"),
    path("nutrient/macros", views.get_macro_breakdown, name="macros"),
    path("nutrient/minerals", views.get_mineral_breakdown, name="minerals"),
    path("nutrient/vitamins", views.get_vitamin_breakdown, name="vitamins"),
    path("graph/macro/completion", views.get_macro_completion, name="macro-completion"),
    path("graph/mineral/completion", views.get_mineral_completion, name="mineral-completion"),
    path("graph/vitamin/completion", views.get_vitamin_completion, name="vitamin-completion"),
]
